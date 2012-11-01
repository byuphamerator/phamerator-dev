#!/usr/bin/env python

import urllib2, os, sys, threading
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dialogs.dialogs import *
import db_conf

class dbStatus(threading.Thread):
  def __init__(self, username, password, server, database, shared, force=False):
    threading.Thread.__init__(self)
    self.username = username
    self.password = password
    self.server = server
    if self.server.startswith('http://'):
      self.server = self.server[7:]
    self.db = database
    self.shared = shared
    self.force = force
  def updateDB(self, user, password, server, db):
    home = os.environ['HOME']
    fname = '%s/.phamerator/%s.sql' % (home, db)

    try:
      # if this is an autoupdate (not a forced manual one) get a new .sql file from the server
      # otherwise we'll just use the local copy that we downloaded at the last autoupdate
      if self.force:
        print 'updating from local .sql file'
      else:
        self.shared.text = 'Downloading updates...'
        f = urllib2.urlopen('http://%s/%s.sql' % (server, db), timeout=100)
        print 'using urllib2 to grab %s.sql' % db
        local_file = open(fname, 'w')
        local_file.write(f.read())
        local_file.close()
    except:
      print 'No remote database is available.  Sticking with the local version.'
      return

    self.shared.text = 'Applying updates...'

    have_root_credentials = False
    try:
      rootdbc = db_conf.db_conf(username='root',password='phage', server='localhost', db='mysql')
      r = rootdbc.get_cursor()
      have_root_credentials = True
    except:
      pass
    if not have_root_credentials:
      try:
        rootdbc = db_conf.db_conf(username='root',password='', server='localhost', db='mysql')
        r = rootdbc.get_cursor()
        have_root_credentials = True
      except:
        pass
    while not have_root_credentials:
      #try:
        dbSetupWarningDlg = databaseSetupWarningDialog(self.db)
        dbSetupWarningDlg.run()
        print '...'
        try:
          rootdbc = db_conf.db_conf(username='root',password=dbSetupWarningDlg.pwd, server='localhost', db='mysql')
          r = rootdbc.get_cursor()
        except:
          continue
        have_root_credentials = True
      #except:
      #  pass

    r.execute("DROP DATABASE IF EXISTS %s_temp" % self.db)
    r.execute("CREATE DATABASE %s_temp" % self.db)

    r.execute("GRANT ALL ON %s_temp.* TO anonymous@localhost IDENTIFIED BY 'anonymous'" % self.db)
    r.execute("FLUSH PRIVILEGES")

    os.system("mysql -u %s -p'%s' %s_temp < %s" % (user, password, db, fname)) # install to a new temp database

  def run(self):
    self.shared.text = 'Checking for database update...'
    user = self.username
    password = self.password
    server = self.server
    db = self.db
    print 'downloading md5sum for %s...' % db
    print 'http://%s/%s.md5sum' % (server, db)
    try:
      f = urllib2.urlopen('http://%s/%s.md5sum' % (server, db))
      md5sum_remote = f.read().split()[0]

      home = os.environ['HOME']
      if not os.path.exists('%s/.phamerator' % home):
        print 'creating .phamerator directory...'
        os.mkdir('%s/.phamerator' % home)
      #print 'dumping local %s database to a file...' % db
      print 'checking local %s database file...' % db
      # skip the local mysqldump, and just check to see if the local (previously downloaded)
      # dumpfile matches the one from the server
      #if not os.path.exists('%s/.phamerator/%s.sql' % (home, db)):
      mysqldump_cmd = "mysqldump -u %s -p'%s' --skip-comments %s > %s/.phamerator/%s.sql" % (user, password, db, home, db)
      #try:
      #  os.system(mysqldump_cmd)
      #except:
      #  print 'error running %s' % mysqldump_cmd
      #print 'dumping finished'

      #if not os.path.exists('%s/.phamerator/%s.sql' % (home, db)):
      #  print 'local database %s could not be dumped.  Is the database server running?' % db
      # sys.exit()

      import md5
      print 'calculating md5sum...'
      try:
		local = open('%s/.phamerator/%s.sql' % (home, db)).read()
      except:
        local = ''
      m = md5.new()
      m.update(local)
      md5sum_local = m.hexdigest()
      print 'calculating finished'
      print md5sum_local, md5sum_remote
      if md5sum_local != md5sum_remote:
        print 'Local database is out of date...downloading...'

        import pygtk
        pygtk.require('2.0')
        import pynotify
        import sys
  
        if not pynotify.init("Phamerator"):
          print 'cannot notify'
  
        n = pynotify.Notification("Phamerator", "Beginning database update", os.path.abspath(os.path.join(os.path.dirname(__file__), 'pixmaps/phamerator.png')))
        if not n.show():
          print "Failed to send notification"

        self.updateDB(user, password, server, db)
        n.update("Phamerator", "Database update complete", os.path.abspath(os.path.join(os.path.dirname(__file__), 'pixmaps/phamerator.png')))
  
        if not n.show():
          print "Failed to send notification"


        self.shared.text = 'database update complete'

      elif self.force:
        print "Updating database at user's request"
        #print 'thread event: %s' % self.updateCompleteEvent
        self.updateDB(user, password, server, db)
        self.shared.text = 'database update complete'

        #self.updateCompleteEvent.set()
        #print 'thread event: %s' % self.updateCompleteEvent
        print "done updating at user's request"
      else:
        print 'local and remote databases are identical'
        self.shared.text = 'database is already the newest version'
        #self.updateCompleteEvent.set()
    except: 
      import sys
      print "Unexpected error:", sys.exc_info()
      print "can't contact the server.  using local copy even though it might be out of date"
      pass

class dbUpdater():
  def __init__(self, database):
    self.database = database
    
  def apply(self):
    have_root_credentials = False
    try:
      rootdbc = db_conf.db_conf(username='root',password='phage', server='localhost', db='mysql')
      r = rootdbc.get_cursor()
      have_root_credentials = True
    except:
      pass
    if not have_root_credentials:
      try:
        rootdbc = db_conf.db_conf(username='root',password='', server='localhost', db='mysql')
        r = rootdbc.get_cursor()
        have_root_credentials = True
      except:
        pass
    while not have_root_credentials:
      #try:
      print 'try to open database setup dialog'
      dbSetupWarningDlg = databaseSetupWarningDialog(self.database)
      dbSetupWarningDlg.run()
      try:
        rootdbc = db_conf.db_conf(username='root',password=dbSetupWarningDlg.pwd, server='localhost', db='mysql')
        r = rootdbc.get_cursor()
      except:
        continue
      have_root_credentials = True
      #except:
      #  pass
    r.execute("SELECT DISTINCT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='%s_temp'" % self.database)
    tables = [row[0] for row in r.fetchall()]
    
    #r.execute("SET foreign_key_checks = 0")
    r.execute("DROP DATABASE IF EXISTS %s" % self.database)
    r.execute("CREATE DATABASE %s" % self.database)
    print 'renaming tables...'
    for table in tables:
      print "RENAME TABLE %s_temp.%s TO %s.%s" % (self.database, table, self.database, table)
      r.execute("RENAME TABLE %s_temp.%s TO %s.%s" % (self.database, table, self.database, table))
    print '...done renaming tables'
    r.execute("GRANT ALL ON %s.* TO anonymous@localhost IDENTIFIED BY 'anonymous'" % self.database)
    #r.execute("SET foreign_key_checks = 1")
    r.execute("FLUSH PRIVILEGES")
    return True
