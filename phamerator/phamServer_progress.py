#!/usr/bin/env python

import os, sys, time, db_conf, getopt, getpass

class options:
  def __init__(self, argv):
    try:
      opts, args = getopt.getopt(argv, "hpu:s:d:r:a:", ["help", "password", "user=","server=","database=","refresh=","alignment_type="])
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
      elif opt in ("-u", "--user"):
        self.argDict['user'] = arg
      elif opt in ("-s", "--server"):
        self.argDict['server'] = arg
      elif opt in ("-d", "--database"):
        self.argDict['database'] = arg
      elif opt in ("-a", "--alignment_type"):
        self.argDict['alignment_type'] = arg
      elif opt in ("-r", "--refresh"):
        self.argDict['refresh'] = arg
    if not self.argDict.has_key('password'): self.argDict['password'] = ''
    required_args = ('user', 'server', 'database', 'alignment_type', 'refresh')
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
             -s, --server: address of the server hosting the database
             -d, --database=<database name>: specify the name of the database to access
             -r, --refresh=interval (in seconds) to poll the database for information
             -a, --alignment_type={blast or clustalw}: this argument is required"""

def main():
  opts = options(sys.argv[1:]).argDict
  username, password, database, server = opts['user'], opts['password'], opts['database'], opts['server']
  table = opts['alignment_type']
  db = opts['database']
  poll = int(opts['refresh'])
  c = db_conf.db_conf(username=username, password=password, server=server, db=database).get_cursor()
  c.execute("SELECT COUNT(*) FROM %s.gene" % db)
  total = int(c.fetchone()[0])
  #print "total:", total
  pbar = os.popen("zenity --progress --auto-close --title=\"%s progress\" --text=\"\"" % table, "w", 0)
  timer = poll
  while 1:
    if timer == poll:
      c.execute("SELECT COUNT(*) FROM %s.gene WHERE %s_status = 'done'" % (db, table))
      count = int(c.fetchone()[0])
      c.execute("COMMIT")
      p = float(count)/total*100
      percent = "%.02f" % p
      pbar.write(str(percent)+'\n')
      timer = 0
    refresh = str(abs((int(timer)-int(poll))))
    pbar.write('#'+str(count)+'/'+str(total)+' genes processed.  '+table+' is ' +str(percent)+'% completed.  Refreshing in '+refresh+' seconds...'+'\n')
    timer = timer + 1
    time.sleep(1)
    
    
if __name__ == '__main__':
    main()
