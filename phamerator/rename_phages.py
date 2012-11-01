#!/usr/bin/env python

import db_conf, string, MySQLdb, getopt, getpass, sys

def usage():
  '''Prints program usage information'''
  print """rename_phages.py [OPTION] [ARGUMENT]
           -h, --help: print this usage information
           -u, --user: specify your username for the database
           -p, --password: prompt for a database password
           -s, --server=<server name>: specify the address of the server where the database is located
           -d, --database=<database name>: specify the name of the database to access"""

def get_options(argv):
  try:
    opts, args = getopt.getopt(argv, "hpu:s:d:", ["help", "password", "user=", "server=", "database="])
  except getopt.GetoptError:
    usage()
  argDict = {}
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    elif opt in ("-p", "--password"):
      argDict['password'] = getpass.getpass("database password: ")
    elif opt in ("-u", "--user"):
      argDict['username'] = arg
    elif opt in ("-d", "--database"):
      argDict['database'] = arg
    elif opt in ("-s", "--server"):
      argDict['server'] = arg

  return argDict

argDict = get_options(sys.argv[1:])

c = db_conf.db_conf(username=argDict['username'], password = argDict['password'], server=argDict['server'], db=argDict['database']).get_cursor()

c.execute("SELECT PhageID, name FROM phage")
results = c.fetchall()
for PhageID, name in results:
  print PhageID, name
  if name.find(' ') > -1:
    name = name.split(' ')
    print name[-1]
    c.execute("UPDATE phage SET name = '%s' WHERE PhageID = '%s'" % (name[-1], PhageID))
c.execute("COMMIT")
