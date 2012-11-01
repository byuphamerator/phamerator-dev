#!/usr/bin/env python

import Pyro.core
import Pyro.naming
import string
import MySQLdb
import time
import random
import threading
import db_conf
import sys
import md5
import logger
from threading import Thread
from Pyro.EventService.Clients import Subscriber
from Pyro.protocol import getHostname

Pyro.config.PYRO_NS_HOSTNAME=getHostname()

keep_alive = True
lowestAvailID = 1
if len(sys.argv) < 2:
  print 'usage: phamServer.py server_instances logging {0|1} {clustalw|blast}'
  sys.exit()
server_instances = int(sys.argv[1])

class NameServer(Thread):
  def __init__(self):
    Thread.__init__(self)
    self.setDaemon(1)
    self.starter = Pyro.naming.NameServerStarter()  # no special identification
  def run(self):
    print "Launching Pyro Name Server"
    self.starter.start(hostname=Pyro.config.PYRO_NS_HOSTNAME)
  def waitUntilStarted(self):
    return self.starter.waitUntilStarted()

class EventServer(Thread):
  def __init__(self):
    Thread.__init__(self)
    self.setDaemon(1)
    self.starter = Pyro.EventService.Server.EventServiceStarter()  # no special identification
  def run(self):
    print "Launching Pyro Event Server"
    self.starter.start(hostname=Pyro.config.PYRO_NS_HOSTNAME)
  def waitUntilStarted(self):
    return self.starter.waitUntilStarted()

class errorHandler:
  def __init__(self):
    self._logger = logger.logger(sys.argv[2])
  def show_sql_errors(self, c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      self._logger.log(error)

class phamServlet(Pyro.core.SynchronizedObjBase, errorHandler):
  def __init__(self):
    Pyro.core.SynchronizedObjBase.__init__(self)
    errorHandler.__init__(self)
    self._logger = logger.logger(sys.argv[2])
    self.lastAccessed = time.time()
    self.name = ''
    self.c = db_conf.db_conf().get_cursor()
    #self.c.execute("SELECT id FROM scores LIMIT 1000")
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
  def get_last_accessed(self):
    #print 'returning lastAccessed'
    return self.lastAccessed

class clustalwServlet(phamServlet, Subscriber, Thread):
  def __init__(self):
    phamServlet.__init__(self)
    Subscriber.__init__(self)
    Thread.__init__(self)
    self.subscribe("clustalw")
    #self.current_db = BLASTdb()
    self.lastAccessed = time.time()
    self.waitTime = random.randint(5,15)
    self.busy = False
    self._logger = logger.logger(sys.argv[2])
    self.c = db_conf.db_conf().get_cursor()
  def ping(self, hostname):
    self._logger.log('received ping from ' + hostname)
  def report_scores(self, id_score, server, hostname):
    global lowestAvailID
    start = time.time()
    self.lastAccessed = time.time()
    self._logger.log('receiving scores from ' + hostname + ' using ' + server)
    #print 'id_score:', id_score
    #print 'id_score[-1:][0]:', id_score[-1:][0]
    if lowestAvailID < int(id_score[-1:][0][0]):
      lowestAvailID = int(id_score[-1:][0][0]) + 1
      self._logger.log('Lowest id available: %s' % lowestAvailID)

    for item in id_score:
      id, score = item
      if score < 0.0 or score > 1.0: 
        # maybe raise an exception?
        self._logger.log('error inserting row')
      else:
        # add the alignment score to the database
        try: self.c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
        except: self.show_sql_errors(self.c)
        node_id = self.c.fetchone()
        if node_id:
          node_id = int(node_id[0])
        else:
          self._logger.log(hostname + 'has no node_id but should')
        try:
          self.c.execute("""UPDATE clustalw SET score = ROUND(%s,4), status = 'done', node_id = '%s'  WHERE id = %s""" % (score, node_id, id))
        except:
          self.show_sql_errors(self.c)
          self._logger.log('id: ' + str(id) + ' score: ' + str(score) + ' node_id: ' + str(node_id))
    try: self.c.execute("""COMMIT""")
    except: sql_show_errors(self.c)
    self._logger.log(hostname + ' --> report_scores: ' + str(time.time() - start))

  def request_seqs(self, server, numSeqs, hostname):
    global lowestAvailID
    self.lastAccessed = time.time()
    self._logger.log('receiving request for ' + str(numSeqs) + ' sequences to align from ' + hostname + ' using ' + server)
    #try: self.c.execute("SELECT query_subject.id, query_subject.query, query_subject.subject FROM query_subject, clustalw WHERE query_subject.id = clustalw.id AND query_subject.id >= %s AND clustalw.status = 'avail' LIMIT %s" % (lowestAvailID, numSeqs))
    try: self.c.execute("SELECT query.GeneID, subject.GeneID, query.clustalw_id AS query_id FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id >= %s AND clustalw.status = 'avail' AND clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' LIMIT %s" % (lowestAvailID, numSeqs))
    except: self.show_sql_errors(self.c)
    seqsToAlign= []
    start = time.time()
    result = self.c.fetchall()
    #print result
    # if no alignments are available, reset the lowestAvailID counter if case some were skipped and try again
    if len(result) == 0:
      lowestAvailID = 1
      return []
    for row in result:
      query, subject, id = row
      #print 'marking', id, 'as pending'
      try: self.c.execute("""UPDATE clustalw SET status = 'pending' WHERE id = %s""" % (id))
      except: self.show_sql_errors(self.c)
    #try: self.c.execute("""UNLOCK TABLES""")
    #except: sql_show_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)

    for row in result:
      query, subject, id = row
      try: self.c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (query))
      except: self.show_sql_errors(self.c)
      querySeq = self.c.fetchone()[0]
      try: self.c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (subject))
      except: self.show_sql_errors(self.c)
      #print 'trying to get subjectSeq'
      subjectSeq = self.c.fetchone()[0]
      #print 'got it'
      seqsToAlign.append((id, querySeq, subjectSeq))
    #seqsToAlign.append((id, querySeq, subjectSeq))
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
    self._logger.log(hostname + ' --> getting seqs: ' + str(time.time() - start))
    return seqsToAlign

class BLASTdb:
  def __init__(self):
    self.c = db_conf.db_conf().get_cursor()
  def get_fasta_data(self):
    '''returns a dictionary: key data contains a string, key md5 contains its hexdigest'''
    try: self.c.execute("""SELECT GeneID, translation FROM gene""")
    except: self.show_sql_errors(self.c)
    results = self.c.fetchall()
    fastaDB = {}
    fasta_data = ''
    for GeneID, translation in results:
      fasta_data = fasta_data + '>' + GeneID + '\n' + translation + '\n'
    fastaDB['data'] = fasta_data
    hash = md5.new()
    hash.update(fasta_data)
    fastaDB['md5'] = hash.hexdigest()
    return fastaDB

class blastServlet(phamServlet, Subscriber, Thread):
  def __init__(self):
    phamServlet.__init__(self)
    Subscriber.__init__(self)
    Thread.__init__(self)
    self.db = db_conf.db_conf()
    self.conn = self.db.get_conn()
    self.c = self.db.get_cursor()
    self.subscribe("fasta")
    self.current_db = BLASTdb().get_fasta_data()
    self.lastAccessed = time.time()
    self.waitTime = random.randint(5,15)
    self.busy = False
    self._logger = logger.logger(sys.argv[2])
  def disconnect(self, client):
    self._logger.log(client + ' has disconnected.  Unlocking tables.')
    try: self.c.execute("ROLLBACK")
    except: self.show_sql_errors(self.c)
    try: self.c.execute("UNLOCK TABLES")
    except: self.show_sql_errors(self.c)
  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
    if event.subject == 'fasta' and event.msg == 'update available': self.update_db()
  def create_view(self, hostname, GeneIDs):
    hostname = hostname.replace('.', '_').replace('-','_')
    sqlQuery = "DROP VIEW IF EXISTS %s" % hostname
    try: self.c.execute(sqlQuery)
    except: self.show_sql_errors(self.c)
    sqlQuery = "CREATE VIEW %s AS SELECT query.GeneID AS query_GeneID, subject.GeneID AS subject_GeneID, query.blast_id AS blast_id FROM alignment as query, alignment as subject WHERE query.GeneID IN (%s) AND query.type = 'Q' AND subject.type = 'S'" % (hostname, GeneIDs)
    #print sqlQuery
    try: self.c.execute(sqlQuery)
    except: self.show_sql_errors(self.c)

  def create_temp_table(self, hostname, GeneIDs):
    hostname = hostname.replace('.', '_').replace('-','_')
    sqlQuery = "DROP TABLE IF EXISTS %s" % hostname
    try: self.c.execute(sqlQuery)
    except:
      self._logger.log('failed query: ' + sqlQuery)
      self.show_sql_errors(self.c)
    sqlQuery = "CREATE TEMPORARY TABLE %s ( query_GeneID VARCHAR(15) NOT NULL, subject_GeneID VARCHAR(15) NOT NULL, blast_id INT(11) UNSIGNED NOT NULL) ENGINE=MEMORY" % hostname
    try: self.c.execute(sqlQuery)
    except:
      self._logger.log('failed query: ' + sqlQuery)
      self.show_sql_errors(self.c)
    sqlQuery = "INSERT INTO %s (query_GeneID, subject_GeneID, blast_id) SELECT query.GeneID AS query_GeneID, subject.GeneID AS subject_GeneID, query.blast_id AS blast_id FROM alignment as query, alignment as subject WHERE query.blast_id = subject.blast_id AND query.GeneID IN (%s) AND query.type = 'Q' AND subject.type = 'S'" % (hostname, GeneIDs)
    #for GeneID in GeneIDs:
    #  sqlQuery = "INSERT INTO %s (query_GeneID, subject_GeneID, blast_id) SELECT query.GeneID AS query_GeneID, subject.GeneID AS subject_GeneID, query.blast_id AS blast_id FROM alignment as query, alignment as subject WHERE query.blast_id = subject.blast_id AND query.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (hostname, GeneID)
    #  self._logger.log(sqlQuery)
      #sqlQuery = "INSERT INTO %s (query_GeneID, subject_GeneID, blast_id) VALUES ('a','b',1)" % (hostname)
    try: self.c.execute(sqlQuery)
    except:
      self._logger.log('failed query: ' + sqlQuery)
      self.show_sql_errors(self.c)

  def request_seqs(self, server, numSeqs, hostname):
    global lowestAvailID
    self.lastAccessed = time.time()
    start = time.time()
    '''returns a python list of GeneIDs to use as queries, or an amt of time to sleep if busy'''
    self._logger.log("""receiving request for %s query IDs from %s using %s""" % (numSeqs, hostname, server))
    # clients should wait an exponentially increasing amount of time to let the busy server update its DB
    #if self.busy:
    #  self.waitTime = self.waitTime * 2
    #  return int(self.waitTime)
    try: self.c.execute("""SELECT COUNT(*) FROM gene""")
    except: self.show_sql_errors(self.c)
    size = self.c.fetchone()[0]
    self._logger.log('number of genes in database: ' + str(size))
    results = []
    low = lowestAvailID
    high = lowestAvailID + (numSeqs * 10000) 
    self.c.execute("LOCK TABLES alignment WRITE, blast WRITE")
    while len(results) == 0:
      sqlQuery =  """SELECT DISTINCT alignment.GeneID FROM alignment, blast WHERE alignment.type = 'Q' AND blast.status = 'avail' AND blast.id BETWEEN %s AND %s AND alignment.blast_id = blast.id LIMIT %s""" % (low, high, numSeqs) 
      #print sqlQuery
      #sqlQuery = """SELECT query FROM (SELECT query, blast1.id FROM query_subject, blast AS blast1 WHERE blast1.id BETWEEN %s AND %s AND blast1.status = 'avail' AND query_subject.id=blast1.id GROUP BY query UNION SELECT query, blast2.id FROM subject_query, blast AS blast2 WHERE blast2.id BETWEEN %s AND %s AND blast2.status = 'avail' AND subject_query.id=blast2.id GROUP BY query) AS junk LIMIT %s FOR UPDATE""" % (low, high, low, high, numSeqs)
      while 1:
        try:
          self.c.execute(sqlQuery)
          break
        except:
          self._logger.log('Retrying the following query due to an error.')
          print sqlQuery
          self.show_sql_errors(self.c)
      results = self.c.fetchall()
      if low >= (size*(size-1)):
        break
      low = high
      high = high * 1.5
    queryIDs = []
    # no query GeneIDs were found, so reset lowestAvailID to 1.  The client should wait and then retry.
    if len(results) == 0:
      lowestAvailID = 1
      self._logger.log('returning empty list')
      self.c.execute("UNLOCK TABLES")
      return []

    IDsToUpdate = []
    for row in results:
      query = row[0]
      #try: self.c.execute("""SELECT id FROM query_subject WHERE query = '%s' UNION SELECT id FROM subject_query WHERE query = '%s'""" % (query, query))
      sqlQuery = """SELECT blast_id FROM alignment WHERE GeneID = '%s' AND type = 'Q'""" % query
      #print sqlQuery
      try: self.c.execute(sqlQuery)
      except: self.show_sql_errors(self.c)
      alignments = self.c.fetchall()
      for alignment in alignments:
        IDsToUpdate.append(str(alignment[0]))
    IDsToUpdate = string.join(IDsToUpdate, ",")
    self._logger.log('marking alignments as pending')
    try: self.c.execute("""UPDATE blast SET status = 'pending' WHERE id IN (%s)""" % IDsToUpdate)
    except: self.show_sql_errors(self.c)
    #try: self.c.execute("COMMIT")
    #except: self.show_sql_errors(self.c)
    self.c.execute("UNLOCK TABLES")
    for GeneID in results:
      queryIDs.append(GeneID[0])
    #print 'queryIds to return:', queryIDs
    self._logger.log(server + ':' + ' returning ' + string.join(queryIDs, ', ') + ' to ' + hostname)
    #self.create_view(hostname, "'" + string.join(queryIDs, "','") + "'")
    #self._logger.log("creating view '" + hostname + "'")
    self._logger.log("creating temporary table '" + hostname + "'")
    self.create_temp_table(hostname, "'" + string.join(queryIDs, "','") + "'")
    #self.create_temp_table(hostname, queryIDs)
    self._logger.log(hostname + ' --> getting seqs: ' + str(time.time() - start))
    return queryIDs

  def report_non_matching_queries(self, nonmatchingQueries, server, hostname):
    nmq = "'" + string.join(nonmatchingQueries, "','") + "'"
    self._logger.log("""receiving queries with no results from %s using %s: '%s'""" % (hostname, server, nmq))
    #print 'nmq:', nmq
    #q = ("""SELECT id FROM query_subject WHERE query IN ('%s') UNION SELECT id FROM subject_query WHERE query IN ('%s')""" % (nmq, nmq))
    self._logger.log("getting ids for non-matching queries")
    q = """SELECT blast_id FROM alignment WHERE GeneID in (%s) AND type = 'Q'""" % nmq
    self._logger.log('done')
    try: self.c.execute(q)
    except:
      self._logger.log('The following query generated an error: ' + q)
      self.show_sql_errors(self.c)
    results = self.c.fetchall()
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)

    done_ids = []
    for result in results: done_ids.append(str(result[0]))
    self._logger.log('Marking ' + str(len(done_ids)) + ' queries with no significant blast results as done')
    #done_ids = string.join(done_ids, ",") # convert the list of done_ids to a string to use in a SQL statement
    done_ids = "'" + string.join(done_ids, "','") + "'"
    #self._logger.log('marking alignments as done')
    q = "UPDATE blast SET status = 'done' WHERE id IN (%s)" % done_ids
    try: self.c.execute(q)
    except:
      print 'failed query:', q
      self.show_sql_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
    self._logger.log('done')

  def report_scores(self, query_subject_score, server, hostname):
    '''adds scores to MySQL database'''
    global lowestAvailID
    self._logger.log('receiving scores from %s using %s' % (hostname, server))
    start = time.time() # to figure out how long the updates take

    # list of ids returned.  This will be used to update lowestAvailID
    ids = []

    # Make sure that reported query/subject pairs are in the alignment table
    uniqueQueries = []
    for query, subject, score in query_subject_score:
      if query not in uniqueQueries: uniqueQueries.append(query)
      #try: self.c.execute("SELECT id FROM query_subject WHERE query = '%s' AND subject = '%s' UNION SELECT id FROM subject_query WHERE query = '%s' AND subject = '%s'" % (query, subject, query, subject))
      #try: self.c.execute("SELECT query.blast_id FROM alignment AS query, alignment AS subject WHERE query.blast_id = subject.blast_id AND query.type = 'Q' AND subject.type = 'S' AND query.GeneID = '%s' AND subject.GeneID = '%s'" % (query, subject))
      h = hostname.replace('.','_').replace('-','_')
      sqlQuery = "SELECT blast_id FROM %s WHERE query_GeneID = '%s' AND subject_GeneID = '%s'" % (h, query, subject)
      try: self.c.execute(sqlQuery)
      except: self.show_sql_errors(self.c)
      results = self.c.fetchone()
      if not results:
        # This shouldn't happen, so exit if it does
        self._logger.log("No id found for query '%s' and subject '%s'" % (query, subject))
        sys.exit()

      # update the database with the returned scores
      id = int(results[0])
      ids.append(id)
      try: self.c.execute("""UPDATE blast SET score = %s WHERE id = '%s'""" % (score, id))
      except: self.show_sql_errors(self.c)
      #try: self.c.execute("COMMIT")
      #except: self.show_sql_errors(self.c)

    for uq in uniqueQueries:
      # Get ids to mark as 'done'.  These are all records with blast.id matching the returned id, even if no score was returned
      # (scores won't get returned for the really crappy alignments)
      #try: self.c.execute("SELECT id FROM query_subject WHERE query = '%s' UNION SELECT id FROM subject_query WHERE query = '%s'" % (uq, uq))
      try: self.c.execute("SELECT blast_id FROM alignment WHERE GeneID = '%s' AND type = 'Q'" % uq)
      except: self.show_sql_errors(self.c)
      results = self.c.fetchall()

      # Mark records as 'done'.
      done_ids = []
      for result in results: done_ids.append(str(result[0]))
      self._logger.log('Marking ' + str(len(done_ids)) + ' queries with significant blast results as done')
      done_ids = "'" + string.join(done_ids, "','") + "'"
      #done_ids = string.join(done_ids, ",") # convert the list of done_ids to a string to use in a SQL statement
      #self._logger.log('marking alignments as done')
      try: self.c.execute("UPDATE blast SET status = 'done' WHERE id IN (%s) AND status != 'done'" % done_ids)
      except: self.show_sql_errors(self.c)
      self._logger.log(str(int(self.conn.affected_rows())) + ' rows were updated')
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      #try: self.c.execute("SELECT COUNT(*) FROM blast WHERE status = 'done' AND id IN (%s)" % done_ids)
      #except: self.show_sql_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)

    self.c.execute("""SELECT COUNT(*) FROM blast WHERE status = 'avail'""")
    avail = self.c.fetchall()
    self.c.execute("""SELECT COUNT(*) FROM blast WHERE status = 'done'""")
    done = self.c.fetchall()
    self.c.execute("""SELECT COUNT(*) FROM blast WHERE status = 'pending'""")
    pending = self.c.fetchall()
    self.c.execute("""SELECT COUNT(*) FROM blast WHERE status = 'stale'""")
    stale = self.c.fetchall()
    self._logger.log("avail: " + str(avail[0][0]) + " done: " + str(done[0][0]) + " pending: " + str(pending[0][0]) + " stale: " + str(stale[0][0]))

    # update lowestAvailID, if needed
    if len(ids) == 0: return 
    ids.sort()
    new_high_id = ids.pop()
    if lowestAvailID < new_high_id:
      lowestAvailID = new_high_id
      self._logger.log('Lowest id available: %s' % lowestAvailID)
    self._logger.log(hostname + ' --> report_scores: ' + str(time.time() - start))

  def check_if_current_db(self, hexdigest):
    '''compares an md5.hexdigest from the client with the one on the server'''
    print 'server:', self.current_db['md5'], 'client:', hexdigest
    if self.current_db['md5'] == hexdigest: return True
    else: return False
  def get_latest_db(self):
    '''returns the current BLAST database as a dictionary'''
    return self.current_db
  def update_db(self):
    '''update the BLAST database dictionary'''
    self._logger.log('fasta update available')
    self.busy = True
    self.current_db = BLASTdb().get_fasta_data()
    self.busy = False
  def run(self):
    self.listen()

class checkStaleRows (threading.Thread, errorHandler):
  def run (self):
    self.c = db_conf.db_conf().get_cursor()
    self._logger = logger.logger(sys.argv[2])
    prevStale = []
    global keep_alive
    while 1:
      #print 'looking for stale alignments...'
      try: self.c.execute("SELECT COUNT(*) FROM clustalw WHERE status = 'stale'")
      except: self.show_sql_errors(self.c)
      s = self.c.fetchone()
      if s: self._logger.log('Adding ' + str(int(s[0])) + ' stale clustalw alignments back to the queue.')
      try: self.c.execute("UPDATE clustalw SET status = 'avail' WHERE status = 'stale'")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      #print 'looking for pending alignments...'
      try: self.c.execute("SELECT COUNT(*) FROM clustalw WHERE status = 'pending'")
      except: self.show_sql_errors(self.c)
      p = self.c.fetchone()
      if p: self._logger.log('Marking ' + str(int(p[0])) + ' pending clustalw alignments as stale.')
      try: self.c.execute("UPDATE clustalw SET status = 'stale' WHERE status = 'pending'")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("SELECT COUNT(*) FROM blast WHERE status = 'stale'")
      except: self.show_sql_errors(self.c)
      s = self.c.fetchone()
      if s: self._logger.log('Adding ' + str(int(s[0])) + ' stale blast alignments back to the queue.')
      try: self.c.execute("UPDATE blast SET status = 'avail' WHERE status = 'stale'")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      #print 'looking for pending alignments...'
      try: self.c.execute("SELECT COUNT(*) FROM blast WHERE status = 'pending'")
      except: self.show_sql_errors(self.c)
      p = self.c.fetchone()
      if p: self._logger.log('Marking ' + str(int(p[0])) + ' pending blast alignments as stale.')
      try: self.c.execute("UPDATE blast SET status = 'stale' WHERE status = 'pending'")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      for i in range(96):
        if not keep_alive:
          return
        time.sleep(5)

class serverSelector(Pyro.core.ObjBase, errorHandler):
  def __init__(self, daemon):
    Pyro.core.ObjBase.__init__(self)
    self._logger = logger.logger(sys.argv[2])
    self.servers = []
    self.daemon = daemon
    self.c = db_conf.db_conf().get_cursor()
  # make some phamServlet objects that should be able to concurrently access the DB
  def create_servers(self, server_instances):
    for i in range(1,server_instances+1):
      if sys.argv[3] == 'clustalw':
        server = clustalwServlet()
      elif sys.argv[3] == 'blast':
        server = blastServlet()
        server.start()
      else:
        self._logger.log('Command line argument error: please specify \'clustalw\' or \'blast\' as the server type')
        sys.exit()
      server.name = 'phamServlet'+str(i)
      self.servers.append(server)
      # connect the phamServlets to the Pyro name server
      uri=self.daemon.connect(server, server.name)
    self._logger.log('spawning ' + str(server_instances) + ' instances of the server')
    return self.servers

  # assign a phamServlet to a client when it first contacts the server program
  def get_server(self, platform, hostname):
    try: self.c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
    except: self.show_sql_errors(self.c)
    node_id = self.c.fetchone()
    if node_id:
      node_id = int(node_id[0])
  # if this is the first ever connection for this client, add it to the node table
    if not node_id:
      #try: self.c.execute("""LOCK TABLES gene WRITE, scores WRITE, node WRITE""")
      #except: self.show_sql_errors(self.c)
      try: self.c.execute("""INSERT INTO node (platform, hostname) VALUES ('%s', '%s')""" % (platform, hostname))
      except: self.show_sql_errors(self.c)
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      try: self.c.execute("""SELECT id FROM node WHERE platform = '%s' AND hostname = '%s'""" % (platform, hostname))
      except: self.show_sql_errors(self.c)
      #try: self.c.execute("""UNLOCK TABLES""")
      #except: sql_show_errors(self.c)
      node_id = self.c.fetchone()[0]
      self._logger.log('registering new node id:' + str(node_id) + ' platform: ' + platform + ' hostname: ' + hostname)

    # return the server that was accessed the least recently (should be the least busy one)
    dict = {}
    for server in self.servers:
      dict[server.name] = server.get_last_accessed()
    items = dict.items()
    items = [(v, k) for (k, v) in items]
    items.sort()
    items = [(k, v) for (v, k) in items]
    self._logger.log(hostname+ ': use ' + items[0][0])
    return items[0][0]

class phamServer(errorHandler):
  def __init__(self, daemon):
    self._logger = logger.logger(sys.argv[2])
    if Pyro.config.PYRO_MULTITHREADED: self._logger.log('Pyro server running in multithreaded mode')
    self.c = db_conf.db_conf().get_cursor()
    try: self.c.execute("SET AUTOCOMMIT = 0")
    except: self.show_sql_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
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
    try: self.c.execute("UPDATE clustalw SET score = NULL, node_id = NULL, status = 'avail' WHERE status = 'pending' OR status = 'stale'")
    except: self.show_sql_errors(self.c)
    try: self.c.execute("UPDATE blast SET score = NULL, node_id = NULL, status = 'avail' WHERE status = 'pending' OR status = 'stale'")
    except: self.show_sql_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
  def shutdown(self):
    self._logger.log('Disconnecting objects from the Pyro nameserver')
    self.daemon.disconnect(self.servSel)
    self._logger.log('...serverSelector')
    for i in range(len(self.servSel.servers)):
      j = self.servSel.servers.pop(0)
      self._logger.log('...' + j.name)
      self.daemon.disconnect(j)
    for server in self.servSel.servers:
      server.abort()
      #server.join()
  def update_blast_db(self):
    '''listen for event that blast database needs to be updated'''
    pass
  def update_clustal_db(self):
    '''listen for event that clustal database needs to be updated'''
    pass

def main():
  nss=NameServer()
  nss.start()
  nss.waitUntilStarted()          # wait until the NS has fully started.
  ess=EventServer()
  ess.start()
  ess.waitUntilStarted()          # wait until the ES has fully started.

  daemon=Pyro.core.Daemon(host='136.142.141.113')
  #ns=Pyro.naming.NameServerLocator().getNS(host='phagecjw-bio.bio.pitt.edu')
  ns=Pyro.naming.NameServerLocator().getNS(host='djs-bio.bio.pitt.edu')
  daemon.useNameServer(ns)
  pServer = phamServer(daemon)
  _logger = logger.logger(sys.argv[2])

  # run the Pyro loop
  try: daemon.requestLoop()
  # if Cntl-C pressed, exit cleanly
  except KeyboardInterrupt:
    global keep_alive
    keep_alive = False
    pServer.shutdown()
    _logger.log('waiting for all threads to exit')

if __name__ == '__main__':
  main()
