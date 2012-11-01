#!/usr/bin/env python2.5

from phamerator_manage_db import *
from db_conf import *
import SOAPpy, sys

def get_phage_name(PhageID, username, password,server, database):
  c = db_conf(username=username, password=password, server=server, db=database).get_cursor()
  name = get_phage_name_from_PhageID(c, PhageID)
  print 'PhageID -> %s' % name
  return name

port = int(sys.argv[1])
server = SOAPpy.SOAPServer(("hatfull12.bio.pitt.edu", port))
server.registerFunction(get_phage_name)
server.serve_forever()

