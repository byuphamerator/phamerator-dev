#!/usr/bin/env python

import Pyro.core
import Pyro.naming
import MySQLdb
import time
import random
import threading
import db_conf
import sys

keep_alive = True
server_instances = int(sys.argv[1])

class errorHandler:
  def show_sql_errors(self, c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      print error

class phamServlet(Pyro.core.ObjBase, errorHandler):
  def __init__(self):
    Pyro.core.ObjBase.__init__(self)
    self.lastAccessed = time.time()
    self.name = ''
  def get_last_accessed(self):
    return self.lastAccessed
  def report_scores(self, query_subject_score, server, hostname):
    start = time.time()
    c = db_conf.db_conf().get_cursor()
    self.lastAccessed = time.time()
    print 'receiving scores from', hostname, 'using', server
    for item in query_subject_score:
      query, subject, score = item 
      if query == None or subject == None or score < 0.0 or score > 1.0: 
        # maybe raise an exception?
        print 'error inserting row'
      else:
        # add the alignment score to the database
        try: c.execute("""LOCK TABLES node WRITE, scores WRITE""")
        except: self.show_sql_errors(c)
        c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
        node_id = c.fetchone()
        if node_id:
          node_id = int(node_id[0])
        else:
          print hostname, 'has no node_id but should\nExiting...'
          sys.exit()
        try: c.execute("""UPDATE scores SET score = ROUND(%s,4), status = 'done', node_id = '%s'  WHERE query = '%s' AND subject = '%s'""" % (score, node_id, query, subject))
        except:
          show_sql_error(c)
          print 'query:', query, 'subject:', subject, 'score:', score, 'node_id:', node_id
    try: c.execute("""UNLOCK TABLES""")
    except: sql_show_errors(c)
    print 'report_scores:', time.time() - start

  def request_seqs(self, server, numSeqs, hostname):
    self.lastAccessed = time.time()
    print 'receiving request for', numSeqs, 'sequences to align from', hostname, 'using', server
    c = db_conf.db_conf().get_cursor()
    try: c.execute("""LOCK TABLES gene WRITE, scores WRITE""")
    except: self.show_sql_errors(c)
    # this is (or at least was) the slowest query
    c.execute("SELECT query, subject FROM scores WHERE status = 'avail' LIMIT %s", numSeqs)
    seqsToAlign= []
    start = time.time()
    for row in c.fetchall():
      query, subject = row
      c.execute("""UPDATE scores SET status = 'pending' WHERE query = '%s' AND subject = '%s'""" % (query, subject))
      c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (query))
      querySeq = c.fetchone()[0]
      c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (subject))
      subjectSeq = c.fetchone()[0]
      seqsToAlign.append((query, querySeq, subject, subjectSeq))
    try: c.execute("""UNLOCK TABLES""")
    except: sql_show_errors(c)
    print 'getting seqs:', time.time() - start
    return seqsToAlign

class checkStaleRows (threading.Thread, errorHandler):
  def run (self):
    c = db_conf.db_conf().get_cursor()
    prevStale = []
    while 1:
      global keep_alive
      if not keep_alive: break
      print 'looking for stale alignments...'
      try: c.execute("SELECT COUNT(*) FROM scores WHERE status = 'stale'")
      except: show_sql_error(c)
      s = c.fetchone()[0]
      if s: print 'Adding', s, 'stale alignments back to the queue.'
      try: c.execute("UPDATE scores SET status = 'avail' WHERE status = 'stale'")
      except: show_sql_error(c)
      print 'looking for pending alignments...'
      try: c.execute("SELECT COUNT(*) FROM scores WHERE status = 'pending'")
      except: show_sql_error(c)
      p = c.fetchone()[0]
      if p: print 'Marking', p, 'pending alignments as stale.'
      try: c.execute("UPDATE scores SET status = 'stale' WHERE status = 'pending'")
      except: show_sql_error(c)
      print 'done'
      for i in range(48):
        if not keep_alive: break
        time.sleep(5)

class serverSelector(Pyro.core.ObjBase, errorHandler):
  def __init__(self, daemon):
    Pyro.core.ObjBase.__init__(self)
    self.servers = []
    self.daemon = daemon
  # make some phamServlet objects that should be able to concurrently access the DB
  def create_servers(self, server_instances):
    for i in range(1,server_instances+1):
      server = phamServlet()
      server.name = 'phamServlet'+str(i)
      self.servers.append(server)
      # connect the phamServlets to the Pyro name server
      uri=self.daemon.connect(server, server.name)
    print 'spawning', server_instances, 'instances of the server'
    return self.servers

  # assign a phamServlet to a client when it first contacts the server program
  def get_server(self, platform, hostname):
    c = db_conf.db_conf().get_cursor()
    c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
    node_id = c.fetchone()
    if node_id:
      node_id = int(node_id[0])
  # if this is the first ever connection for this client, add it to the node table
    if not node_id:
      try: c.execute("""LOCK TABLES gene WRITE, scores WRITE, node WRITE""")
      except: self.show_sql_errors(c)
      c.execute("""INSERT INTO node (platform, hostname) VALUES ('%s', '%s')""" % (platform, hostname))
      c.execute("""SELECT id FROM node WHERE platform = '%s' AND hostname = '%s'""" % (platform, hostname))
      try: c.execute("""UNLOCK TABLES""")
      except: sql_show_errors(c)
      node_id = c.fetchone()[0]
      print 'registering new node', 'id:', node_id, 'platform:', platform, 'hostname:', hostname

    # return the server that was accessed the least recently (should be the least busy one)
    dict = {}
    for server in self.servers:
      dict[server.name] = server.lastAccessed
    items = dict.items()
    items = [(v, k) for (k, v) in items]
    items.sort()
    items = [(k, v) for (v, k) in items]
    print hostname+':', 'use', items[0][0]
    return items[0][0]

class phamServer(errorHandler):
  def __init__(self, daemon):
    if Pyro.config.PYRO_MULTITHREADED: print 'Pyro server running in multithreaded mode'
    self.reset_stale_rows()
    self.daemon = daemon
    self.servers = []
    self.servSel = serverSelector(self.daemon)
    self.servSel.create_servers(server_instances)
    print 'Registering serverSelector.'
    uri=self.daemon.connect(self.servSel, "serverSelector")
    print 'done'
    checkStaleRows().start()
    print 'Startup complete.  Listening for client connections...'
  def reset_stale_rows(self):
    c = db_conf.db_conf().get_cursor()
    print 'Clearing stale alignments.'
    try: c.execute("UPDATE scores SET score = NULL, node_id = NULL, status = 'avail' WHERE status IN ('pending','stale')")
    except: self.show_sql_errors(c)
  def shutdown(self):
    print '\nDisconnecting objects from the Pyro nameserver'
    self.daemon.disconnect(self.servSel)
    print '...serverSelector'
    for i in range(len(self.servSel.servers)):
      j = self.servSel.servers.pop(0)
      print '...' + j.name
      self.daemon.disconnect(j)

daemon=Pyro.core.Daemon(host='136.142.141.113')
ns=Pyro.naming.NameServerLocator().getNS(host='phagecjw-bio.bio.pitt.edu')
daemon.useNameServer(ns)
pServer = phamServer(daemon)

# run the Pyro loop
try: daemon.requestLoop()
# if Cntl-C pressed, exit cleanly
except KeyboardInterrupt:
  pServer.shutdown()
  keep_alive = False
  print '\nwaiting for all threads to exit'
