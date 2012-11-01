#!/usr/bin/python

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from phamerator import *
from phamerator.phamerator_manage_db import *
from phamerator.pham import *
import getpass
import string


user='root'
server1 = 'djs-bio.bio.pitt.edu'
pwd = getpass.getpass('root database password on %s: ' % server1)
db = raw_input('database 1: ')
d = db_conf.db_conf(username=user,password=pwd,server=server1,db=db)
cOld = d.get_cursor()

server2 = 'phamerator.csm.jmu.edu'
pwd = getpass.getpass('root database password on %s: ' % server2)
db = raw_input('database 2: ')
e = db_conf.db_conf(username=user,password=pwd,server=server2,db=db)
cNew = e.get_cursor()


oC = PhamController(cOld, source='db')
nC = PhamController(cNew, source='db')

oldPhams = oC.get_pham()
newPhams = nC.get_pham()

print '*' * 80
print 'Old Phams'
#print oldPhams
for o in oldPhams:
  if o not in newPhams:
    print o

print '*' * 80

print 'New Phams'
#print newPhams
for n in newPhams:
  if n not in oldPhams:
    print n
print '*' * 80

print oldPhams == newPhams
