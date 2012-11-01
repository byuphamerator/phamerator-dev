#!/usr/bin/env python

import os, sys, time, db_conf, getopt, getpass

class options:
  def __init__(self, argv):
    try:
      opts, args = getopt.getopt(argv, "hpu:s:d:o:a:", ["help", "password", "user=","server=","database=","poll=","alignment_type="])
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
      elif opt in ("-o", "--poll"):
        self.argDict['poll'] = arg
    if not self.argDict.has_key('password'): self.argDict['password'] = ''

  def usage(self):
    '''Prints program usage information'''
    print """phamServer_InnoDB.py [OPTION] [ARGUMENT]
             -h, --help: print this usage information
             -u, --user=<username>: specify a username on the database
             -p, --password: prompt for a password
             -s, --server: address of the server hosting the database
             -d, --database=<database name>: specify the name of the database to access
             -a, --alignment_type={blast or clustalw}: this argument is required
             -o, --poll=interval (in seconds) to poll the database for information"""

def main():
  opts = options(sys.argv[1:]).argDict
  username, password, database, server = opts['user'], opts['password'], opts['database'], opts['server']
  table = opts['alignment_type']
  poll = int(opts['poll'])
  c = db_conf.db_conf(username=username, password=password, server=server, db=database).get_cursor()
  c.execute("SELECT COUNT(*) FROM %s" % table)
  total = int(c.fetchone()[0])
  #print "total:", total
  pbar = os.popen("zenity --progress --auto-close --title=\"%s progress\" --text=\"\"" % table, "w", 0)
  timer = poll
  while 1:
    if timer == poll:
      c.execute("SELECT COUNT(*) FROM %s WHERE status = 'done'" % table)
      count = int(c.fetchone()[0])
      c.execute("COMMIT")
      p = float(count)/total*100
      percent = "%02f" % p
      pbar.write(str(percent)+'\n')
      timer = 0
    pbar.write('#'+str(count)+'/'+str(total)+' : '+str(percent)+'% '+str(timer)+'/'+str(poll)+'\n')
    timer = timer + 1
    time.sleep(1)

if __name__ == '__main__':
  main()
