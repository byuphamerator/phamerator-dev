#!/usr/bin/env python2.5

import db_conf
from phamerator_manage_db import *
from getpass import getpass

username = 'steve'
password = getpass()
server = 'djs-bio.bio.pitt.edu'
db = 'Hatfull'

c = db_conf.db_conf(username='steve',password=password,server=server,db=db).get_cursor()

pham_t = get_phams(c)
# keys are pham name, values are # of members
# like this ...   13L : 2
phams = {}
for pham in pham_t:
  if phams.has_key(pham[0]):
    phams[pham[0]] += 1
  else:
    phams[pham[0]] = 1

keys = phams.keys()
keys.sort()
#for key in keys:
#  print key, phams[key]

phams_keyed_by_size = {}

for pham_name in phams.keys():
  if phams_keyed_by_size.has_key(phams[pham_name]):
    phams_keyed_by_size[phams[pham_name]] += 1
  else:
    phams_keyed_by_size[phams[pham_name]] = 1

keys = phams_keyed_by_size.keys()
keys.sort()
for key in keys:
  print key, phams_keyed_by_size[key]
