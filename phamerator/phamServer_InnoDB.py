#!/usr/bin/env python

import Pyro.core
import Pyro.naming
import string
import MySQLdb
import time
import random
import threading
try:
  from phamerator import *
except:
  import sys, os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import alignmentDatabase
from errorHandler import *
import db_conf
import sys
try:
  import hashlib
except ImportError:
  import md5
import getopt
import getpass
import logger
from threading import Thread
from Pyro.EventService.Clients import Subscriber
from Pyro.protocol import getHostname
import Pyro.EventService.Clients

#Pyro.config.PYRO_NS_HOSTNAME=getHostname()
#Pyro.config.PYRO_NS_HOSTNAME='phamerator.csm.jmu.edu'
#Pyro.config.PYRO_NS_HOSTNAME='134.126.95.56'
Pyro.config.PYRO_MAXCONNECTIONS=1000

Pyro.config.PYRO_NS_HOSTNAME='localhost'
#Pyro.config.PYRO_NS_HOSTNAME='136.142.141.113'

class options:
  def __init__(self, argv):
    try:
      opts, args = getopt.getopt(argv, "hps:n:u:d:i:l:a:", ["help", "password", "server=", "nsname=", "user=","database=","instances=","logging=","alignment_type="])
    except getopt.GetoptError:
      print 'error running getopt.getopt'
      self.usage()
    self.argDict = {}
    for opt, arg in opts:
      if opt in ("-h", "--help"):
        self.usage()
        sys.exit()
      elif opt in ("-p", "--password"):
        self.argDict['password'] = getpass.getpass('password: ')
      elif opt in ("-s", "--server"):
      	self.argDict['server'] = arg
      elif opt in ("-n", "--nsname"):
      	self.argDict['nsname'] = arg
      elif opt in ("-u", "--user"):
        self.argDict['user'] = arg
      elif opt in ("-d", "--database"):
        self.argDict['database'] = arg
      elif opt in ("-i", "--instances"):
        self.argDict['instances'] = arg
      elif opt in ("-l", "--logging"):
        self.argDict['logging'] = arg
      elif opt in ("-a", "--alignment_type"):
        self.argDict['alignment_type'] = arg
    if not self.argDict.has_key('password'): self.argDict['password'] = ''
    required_args = ('server', 'nsname', 'user', 'database', 'instances', 'logging', 'alignment_type')
    for a in required_args:
      if a not in self.argDict:
        print "required argument '%s' is missing" % a
        self.usage()
        sys.exit()

  def usage(self):
    '''Prints program usage information'''
    print """phamServer_InnoDB.py [OPTION] [ARGUMENT]
             -h, --help: print this usage information
             -u, --user=<username>: specify a username on the database
             -p, --password: prompt for a password
             -d, --database=<database name>: specify the name of the database to access
             -i, --instances=<number_of_instances>: number of server instances to run (default=1)
             -l, --logging={True or False}: whether to print out debugging info (default is True)
             -a, --alignment_type={blast or clustalw}: this argument is required
             -s, --server=<hostname>: hostname of database server, required
             -n, --nsname=<nsname>: PYRO server nsname, usually localhost, required"""

class phamPublisher(Pyro.EventService.Clients.Publisher):
  '''Publishes Pyro events over the network to clients, for instance when the BLAST database changes'''
  def __init__(self):
    Pyro.EventService.Clients.Publisher.__init__(self)
  #def publish(self, channel, message):
  #  self.publish(channel, message)

class NameServer(Thread):
  def __init__(self):
    Thread.__init__(self)
    self.setDaemon(1)
    self.starter = Pyro.naming.NameServerStarter()  # no special identification
  def run(self):
    print "Launching Pyro Name Server"
    self.starter.start() # (hostname=Pyro.config.PYRO_NS_HOSTNAME)
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

class phamServlet(Pyro.core.SynchronizedObjBase, errorHandler):
  def __init__(self, logging, c):
    Pyro.core.SynchronizedObjBase.__init__(self)
    errorHandler.__init__(self)
    self._logger = logger.logger(logging)
    self.lastAccessed = time.time()
    self.name = ''
    self.c = c
    #self.c.execute("SELECT id FROM scores LIMIT 1000")
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
    
  def get_last_accessed(self):
    #print 'returning lastAccessed'
    return self.lastAccessed

class clustalwServlet(phamServlet, Subscriber, Thread):
  def __init__(self, logging, c, server, database, opts):
    Thread.__init__(self)
    phamServlet.__init__(self,logging, c)
    Subscriber.__init__(self)
    #self.setDaemon(1)
    self.server, self.database = server, database
    self.c = db_conf.db_conf(username=opts['user'], password=opts['password'], server='localhost', db=opts['database']).get_cursor()
    self.subscribe("clustalw")
    self._logger = logger.logger(logging)
    self.publisher = phamPublisher()

  def request_db_info(self):
    '''phamClient needs this info to get a proper database cursor, but it also needs a valid username/password pair'''
    return self.server, self.database

  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
    if event.subject == 'clustalw' and event.msg == 'database has alignments available':
      self._logger.log('telling the clients to get busy')
      self.publisher.publish('clustalw', 'get busy')

  def report_scores(self, clustalw_work_unit, results, client_host):
    '''compute node reporting scores for a particular query'''
    self._logger.log('%s: reporting clustalw results' % client_host)
    clustalw_work_unit.add_matches(results, self.c)

  def request_seqs(self, client_host):
    '''compute node asking for a query sequence and optionally the database for clustalw alignments'''
    self._logger.log('%s: requesting clustalw work unit' % client_host)
    clustalw_work_unit = alignmentDatabase.clustalwWorkUnit(self.c)
    if not clustalw_work_unit.query_id:
      try:
        import pynotify
        if pynotify.init("Phamerator"):
          n = pynotify.Notification("Phamerator Server Update", "Clustalw alignments completed", "file:///%s" % os.path.join(os.path.dirname(__file__),"pixmaps/phamerator.png"))
          n.show()
        else:
          pass
          #print "there was a problem initializing the pynotify module"
      except:
        pass

    return clustalw_work_unit

  def run(self):
    self.listen()

class blastServlet(phamServlet, Subscriber, Thread):
  def __init__(self, logging, c, server, database, opts):
    Thread.__init__(self)
    phamServlet.__init__(self, logging, c)
    Subscriber.__init__(self)
    self.c = db_conf.db_conf(username=opts['user'], password=opts['password'], server='localhost', db=opts['database']).get_cursor()
    self.server, self.database = server, database
    self.subscribe("fasta")
    self.lastAccessed = time.time()
    self.waitTime = random.randint(5,15)
    self.busy = False
    self._logger = logger.logger(logging)
    self.status = 'avail'

  def request_db_info(self):
    '''phamClient needs this info to get a proper database cursor, but it also needs a valid username/password pair'''
    return self.server, self.database

  def disconnect(self, client):
    '''cleans up after a client disconnects'''
    self._logger.log(client + ' has disconnected.  Rolling back changes.')
    try:
      self.c.execute("ROLLBACK")
      self._logger.log('done.')
    except: self.show_sql_errors(self.c)
    self._logger.log(client + ' has disconnected.  Unlocking tables.')
    try:
      self.c.execute("UNLOCK TABLES")
      self._logger.log('done.')
    except: self.show_sql_errors(self.c)

  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
    if event.subject == 'fasta' and event.msg == 'update available': self.update_db()

  def request_seqs(self, client_host):
    '''the new method for getting seqs for BLAST that doesn't use the alignment and blast tables'''
    self.lastAccessed = time.time()
    self._logger.log('%s: requesting BLAST work unit' % client_host)
    blastWorkUnit = alignmentDatabase.blastWorkUnit(self.c)
    return blastWorkUnit

  def report_scores(self, blastWorkUnit, results, client_host):
    '''compute node reporting scores for a particular query'''
    self._logger.log('%s: reporting BLAST results' % client_host)
    self.lastAccessed = time.time()
    blastWorkUnit.add_matches(results, self.c)

  def run(self):
    self.listen()

class checkStaleRows (Thread, errorHandler):
  def __init__(self,logging, c):
    Thread.__init__(self)
    self.setDaemon(1)
    self.logging = logging
    self.c = c

  def run (self):
    self._logger = logger.logger(self.logging)
    while 1:
      self._logger.log('looking for stale clustalw alignments...')
      self.c.execute("UPDATE gene SET clustalw_status = 'avail' WHERE clustalw_status = 'stale'")
      self._logger.log('looking for pending clustalw alignments...')
      self.c.execute("UPDATE gene SET clustalw_status = 'stale' WHERE clustalw_status = 'pending'")
      self._logger.log('looking for stale blast alignments...')
      self.c.execute("UPDATE gene SET blast_status = 'avail' WHERE blast_status = 'stale'")
      self._logger.log('looking for pending blast alignments...')
      self.c.execute("UPDATE gene SET blast_status = 'stale' WHERE blast_status = 'pending'")
      self.c.execute("COMMIT")
      time.sleep(60*60)

class serverSelector(Pyro.core.SynchronizedObjBase, errorHandler):
  def __init__(self, daemon, logging, c, username, password, server, database, opts):
    Pyro.core.SynchronizedObjBase.__init__(self)
    self._logger = logger.logger(logging)
    self.logging = logging
    self.servers = []
    self.setPyroDaemon(daemon)
    self.c = c
    self.username = username
    self.password = password
    self.server = server
    self.database = database
    self.opts = opts

  # make some phamServlet objects that should be able to concurrently access the DB
  def create_servers(self, server_instances, alignment_type, server, database):
    for i in range(1,server_instances+1):
      #if sys.argv[3] == 'clustalw':
      if alignment_type == 'clustalw':
        server = clustalwServlet(self.logging, self.c, server, database, self.opts)
      #elif sys.argv[3] == 'blast':
      elif alignment_type == 'blast':
        server = blastServlet(self.logging, self.c, server, database, self.opts)
        uri=self.daemon.connect(server, server.name)
      else:
        self._logger.log('Command line argument error: please specify \'clustalw\' or \'blast\' as the server type')
        sys.exit()
      server.name = 'phamServlet'+str(i)
      uri=self.daemon.connect(server, server.name)
      self.servers.append(server)
      server.start()
      # connect the phamServlets to the Pyro name server
    self._logger.log('spawning ' + str(server_instances) + ' instances of the server')
    return self.servers

  # assign a phamServlet to a client when it first contacts the server program
  def get_server(self, platform, hostname):
    try:
      self.c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
    except:
      self.c = db_conf.db_conf(username=self.username, password=self.password, server=self.server, db=self.database).get_cursor()
    try:
      self.c.execute("""SELECT id FROM node WHERE hostname = '%s'""" % hostname)
    except:
      self.show_sql_errors(self.c)
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
  def __init__(self, daemon, server_instances, alignment_type, logging, c, username, password, server, database, opts):
    self._logger = logger.logger(logging)
    if Pyro.config.PYRO_MULTITHREADED: self._logger.log('Pyro server running in multithreaded mode')
    self.c = c
    try: self.c.execute("SET AUTOCOMMIT = 0")
    except: self.show_sql_errors(self.c)
    try: self.c.execute("COMMIT")
    except: self.show_sql_errors(self.c)
    #self.reset_stale_rows()
    self.daemon = daemon
    self.servers = []
    self.servSel = serverSelector(self.daemon, logging, self.c, username, password, server, database, opts)
    self.servers = self.servSel.create_servers(server_instances, alignment_type, server, database)
    self._logger.log('Registering serverSelector.')
    uri=self.daemon.connect(self.servSel, "serverSelector")
    self._logger.log('Startup complete.  Listening for client connections...')

  def reset_stale_rows(self):
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
  def update_blast_db(self):
    '''listen for event that blast database needs to be updated'''
    pass
  def update_clustal_db(self):
    '''listen for event that clustal database needs to be updated'''
    pass

def main():
  opts = options(sys.argv[1:]).argDict
  username, password, database, server = opts['user'], opts['password'], opts['database'], opts['server']
  alignment_type = opts['alignment_type']
  print 'username :', username
  #print 'password :', password
  print 'server   :', server
  print 'database :', database
  if opts['nsname']:
    Pyro.config.PYRO_NS_HOSTNAME=opts['nsname']
  nss=NameServer()
  nss.start()
  nss.waitUntilStarted()          # wait until the NS has fully started.
  ess=EventServer()
  ess.start()
  ess.waitUntilStarted()          # wait until the ES has fully started.
  server_instances = int(opts['instances'])
  logging = opts['logging']

  daemon=Pyro.core.Daemon(host=server)
  ns=Pyro.naming.NameServerLocator().getNS(host=server)
  daemon.useNameServer(ns)
  _logger = logger.logger(logging)
  c =         db_conf.db_conf(username=username, password=password, db=database).get_cursor()
  csrCursor = db_conf.db_conf(username=username, password=password, db=database).get_cursor()
  csr = checkStaleRows(logging, csrCursor)
  csr.start()
  pServer = phamServer(daemon, server_instances, alignment_type, logging, c, username, password, server, database, opts)

  # run the Pyro loop
  try: daemon.requestLoop()
  # if Cntl-C pressed, exit cleanly
  except (KeyboardInterrupt, SystemExit):
    pServer.shutdown()
    _logger.log('waiting for all threads to exit')

if __name__ == '__main__':
  main()
