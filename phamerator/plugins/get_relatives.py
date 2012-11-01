#!/usr/bin/env python

from phamerator import *
from phamerator.phamerator_manage_db import *
from phamerator.db_conf import db_conf
import sys, getpass

GeneID = sys.argv[1]
password = getpass.getpass()
db = raw_input('database: ')

c = db_conf(username='root', password=password, server='134.126.132.72', db=db).get_cursor()

print get_relatives(c, GeneID, alignmentType='both', clustalwThreshold=0.275, blastThreshold=0.0001)
