#!/usr/bin/env python

import Pyro.core
import Pyro.naming
import MySQLdb
import time
import random
import threading
import db_conf
import sys
from threading import Thread

keep_alive = True
if len(sys.argv) < 2:
  print 'usage: phamServer.py server_instances'
  sys.exit()
server_instances = int(sys.argv[1])

class logger:
  def __init__(self):
    if len(sys.argv) >= 3: self.shouldLog = sys.argv[2]
    else: self.shouldLog = True
  def log(self, string):
    now = time.localtime(time.time())
    print time.strftime("%m/%d/%y %H:%M:%S:", now), string

class errorHandler:
  def __init__(self):
    self._logger = logger()
  def show_sql_errors(self, c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      self._logger.log(error)

class phamServlet(Pyro.core.ObjBase, errorHandler):
  def __init__(self):
    Pyro.core.ObjBase.__init__(self)
    errorHandler.__init__(self)
    self._logger = logger()
    self.lastAccessed = time.time()
    self.name = ''
  def get_last_accessed(self):
    print 'returning lastAccessed'
    return self.lastAccessed
  def report_scores(self, id_score, server, hostname):
    start = time.time()
    c = db_conf.db_conf().get_cursor()
    self.lastAccessed = time.time()
    self._logger.log('receiving scores from ' + hostname + ' using ' + server)
    for item in id_score:
      id, score = item
      if score < 0.0 or score > 1.0: 
        # maybe raise an exception?
        self._logger.log('error inserting row')
        cont = None
        while cont not in ['Y', 'y', 'N', 'n']:
          cont = raw_input('continue? (y/n)')
          if cont in ['N', 'n']:
            self._logger.log('Exiting per user request.')
            sys.exit()
      else:
        # add the alignment score to the database
        #try: c.execute("""LOCK TABLES node WRITE, scores WRITE""")
        #except: self.show_sql_errors(c)
        c.execute("""SELECT id FROM node WHERE hostname = '%s' FOR UPDATE""" % hostname)
        node_id = c.fetchone()
        if node_id:
          node_id = int(node_id[0])
        else:
          print hostname, 'has no node_id but should\n'
          while cont not in ['Y', 'y', 'N', 'n']:
            cont = raw_input('continue? (y/n)')
            if cont in ['N', 'n']:
              self._logger.log('Exiting per user request.')
              sys.exit()
        try: c.execute("""UPDATE scores SET score = ROUND(%s,4), status = 'done', node_id = '%s'  WHERE id = %s""" % (score, node_id, id))
        except:
          self.show_sql_error(c)
          self._logger.log('id: ' + id + ' score: ' + score + ' node_id: ' + node_id)
    try: c.execute("""COMMIT""")
    except: sql_show_errors(c)
    self._logger.log(hostname + ' --> report_scores: ' + str(time.time() - start))

  def request_seqs(self, server, numSeqs, hostname):
    self.lastAccessed = time.time()
    self._logger.log('receiving request for ' + str(numSeqs) + ' sequences to align from ' + hostname + ' using ' + server)
    c = db_conf.db_conf().get_cursor()
    try: c.execute("""LOCK TABLES scores WRITE""")
    except: self.show_sql_errors(c)
    try: c.execute("SELECT id, query, subject FROM scores WHERE status = 'avail' LIMIT %s", numSeqs)
    except: self.show_sql_errors(c)
    seqsToAlign= []
    start = time.time()
    result = c.fetchall()
    for row in result:
      id, query, subject = row
      #print 'marking', id, 'as pending'
      c.execute("""UPDATE scores SET status = 'pending' WHERE id = %s""" % (id))
    try: c.execute("""UNLOCK TABLES""")
    except: sql_show_errors(c)
    try: c.execute("COMMIT")
    except: self.show_sql_errors(c)

    for row in result:
      id, query, subject = row
      c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (query))
      querySeq = c.fetchone()[0]
      c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (subject))
      subjectSeq = c.fetchone()[0]
      seqsToAlign.append((id, querySeq, subjectSeq))
    seqsToAlign.append((id, querySeq, subjectSeq))
    try: c.execute("COMMIT")
    except: self.show_sql_errors(c)
    self._logger.log(hostname + ' --> getting seqs: ' + str(time.time() - start))
    return seqsToAlign

class BLASTdb:
  def __init__(self):
    pass
  def get_fasta_data(self):
    '''returns a dictionary: key data contains a string, key md5 contains its hexdigest'''
    c = db_conf.db_conf().get_cursor()
    c.execute("""SELECT GeneID, translation FROM gene""")
    results = c.fetchall()
    fastaDB = {}
    fasta_data = None
    for GeneID, translation in results:
      fasta_data = fasta_data + '\n>' + GeneID + '\n' + translation
    fastaDB[data] = fasta_data
    hash = md5.new()
    hash.update(fasta_data)
    fastaDB[md5] = hash.hexdigest()
    return fastaDB

from Pyro.EventService.Clients import Subscriber

class blastServlet(phamServlet, Subscriber, Thread):
  def __init__(self):
    phamServlet.__init__(self)
    Subscriber.__init__(self)
    Thread.__init__(self)
    self.subscribe("fasta")
    self.current_db = BLASTdb()
    self.lastAccessed = time.time()
    self.waitTime = random.randint(5,15)
    self.busy = False
    self._logger = logger()
    self.c = db_conf.db_conf().get_cursor()
  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
  def ping(self):
    print "I'm alive"
  def request_seqs(self, server, numSeqs, hostname):
    '''returns a python list of GeneIDs to use as queries, or an amt of time to sleep if busy'''
    self._logger.log("""receiving request for %s query IDs from %s using %s""" % (numSeqs, hostname, server))
    # clients should wait an exponentially increasing amount of time to let the busy server update its DB
    if self.busy:
      self.waitTime = self.waitTime * 2
      return int(self.waitTime)
    self.c.execute("""SELECT query FROM blast_scores WHERE status = 'avail' LIMIT %s""" % numSeqs)
    queryIDs = []
    for GeneID in c.fetchall():
      queryIDs.append(GeneID[0])
    return queryIDs
  def report_scores(self, query_subject_score, server, hostname):
    '''adds scores to MySQL database'''
    for query, subject, score in query_subject_score:
      self.c.execute("""INSERT INTO blast_scores (query, subject, score) VALUES ('%s', '%s', %s)""" % (query, subject, score))
      # insert into db
  def check_if_current_db(hexdigest):
    '''compares an md5.hexdigest from the client with the one on the server'''
    if self.current_db[md5] == hexdigest: return True
    else: return False
  def get_latest_db():
    '''returns the current BLAST database as a dictionary'''
    return self.current_db
  def update_db():
    '''update the BLAST database dictionary'''
    self.busy = True
    self.current_db = BLASTdb()
    self.busy = False
  def run(self):
    self.listen()

class checkStaleRows (threading.Thread, errorHandler):
  def run (self):
    c = db_conf.db_conf().get_cursor()
    self._logger = logger()
    prevStale = []
    while 1:
      global keep_alive
      if not keep_alive: break
      #print 'looking for stale alignments...'
      try: c.execute("SELECT COUNT(*) FROM scores WHERE status = 'stale' FOR UPDATE")
      except: self.show_sql_errors(c)
      s = c.fetchone()
      if s: self._logger.log('Adding ' + str(int(s[0])) + ' stale alignments back to the queue.')
      try: c.execute("UPDATE scores SET status = 'avail' WHERE status = 'stale'")
      except: self.show_sql_errors(c)
      #print 'looking for pending alignments...'
      try: c.execute("SELECT COUNT(*) FROM scores WHERE status = 'pending' FOR UPDATE")
      except: self.show_sql_errors(c)
      p = c.fetchone()
      if p: self._logger.log('Marking ' + str(int(p[0])) + ' pending alignments as stale.')
      try: c.execute("UPDATE scores SET status = 'stale' WHERE status = 'pending'")
      except: self.show_sql_errors(c)
      try: c.execute("COMMIT")
      except: self.show_sql_errors(c)
      for i in range(48):
        if not keep_alive: break
        time.sleep(5)

class serverSelector(Pyro.core.ObjBase, errorHandler):
  def __init__(self, daemon):
    Pyro.core.ObjBase.__init__(self)
    self._logger = logger()
    self.servers = []
    self.daemon = daemon
  # make some phamServlet objects that should be able to concurrently access the DB
  def create_servers(self, server_instances):
    for i in range(1,server_instances+1):
      #server = phamServlet()
      server = blastServlet()
      server.start()
      #self._logger.log('last accessed: %s' % server.lastAccessed)
      #server.name = 'phamServlet'+str(i)
      server.name = 'blastServlet'+str(i)
      self.servers.append(server)
      # connect the phamServlets to the Pyro name server
      uri=self.daemon.connect(server, server.name)
    self._logger.log('spawning ' + str(server_instances) + ' instances of the server')
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
      #try: c.execute("""LOCK TABLES gene WRITE, scores WRITE, node WRITE""")
      #except: self.show_sql_errors(c)
      c.execute("""INSERT INTO node (platform, hostname) VALUES ('%s', '%s')""" % (platform, hostname))
      c.execute("""SELECT id FROM node WHERE platform = '%s' AND hostname = '%s'""" % (platform, hostname))
      #try: c.execute("""UNLOCK TABLES""")
      #except: sql_show_errors(c)
      node_id = c.fetchone()[0]
      self._logger.log('registering new node id:' + str(node_id) + ' platform: ' + platform + ' hostname: ' + hostname)

    # return the server that was accessed the least recently (should be the least busy one)
    dict = {}
    for server in self.servers:
      dict[server.name] = server.get_last_accessed()
    items = dict.items()
    items = [(v, k) for (k, v) in items]
    items.sort()
    items = [(k, v) for (v, k) in items]
    self._logger.log(hostname+ ': use' + items[0][0])
    return items[0][0]

class phamServer(errorHandler):
  def __init__(self, daemon):
    self._logger = logger()
    if Pyro.config.PYRO_MULTITHREADED: self._logger.log('Pyro server running in multithreaded mode')
    c = db_conf.db_conf().get_cursor()
    try: c.execute("SET AUTOCOMMIT = 0")
    except: self.show_sql_error(c)
    self.reset_stale_rows()
    self.daemon = daemon
    self.servers = []
    self.servSel = serverSelector(self.daemon)
    self.servSel.create_servers(server_instances)
    self._logger.log('Registering serverSelector.')
    uri=self.daemon.connect(self.servSel, "serverSelector")
    checkStaleRows().start()
    self._logger.log('Startup complete.  Listening for client connections...')
  def reset_stale_rows(self):
    c = db_conf.db_conf().get_cursor()
    self._logger.log('Clearing stale alignments.')
    try: c.execute("UPDATE scores SET score = NULL, node_id = NULL, status = 'avail' WHERE status = 'pending' OR status = 'stale'")
    except: self.show_sql_errors(c)
  def shutdown(self):
    self._logger.log('Disconnecting objects from the Pyro nameserver')
    self.daemon.disconnect(self.servSel)
    self._logger.log('...serverSelector')
    for i in range(len(self.servSel.servers)):
      j = self.servSel.servers.pop(0)
      j.abort()
      self._logger.log('...' + j.name)
      self.daemon.disconnect(j)
  def update_blast_db(self):
    '''listen for event that blast database needs to be updated'''
    pass
  def update_clustal_db(self):
    '''listen for event that clustal database needs to be updated'''
    pass

def main():
  daemon=Pyro.core.Daemon(host='136.142.141.113')
  #ns=Pyro.naming.NameServerLocator().getNS(host='phagecjw-bio.bio.pitt.edu')
  ns=Pyro.naming.NameServerLocator().getNS(host='djs-bio.bio.pitt.edu')
  daemon.useNameServer(ns)
  pServer = phamServer(daemon)
  _logger = logger()

  # run the Pyro loop
  try: daemon.requestLoop()
  # if Cntl-C pressed, exit cleanly
  except KeyboardInterrupt:
    pServer.shutdown()
    keep_alive = False
    _logger.log('waiting for all threads to exit')

if __name__ == '__main__':
  main()
