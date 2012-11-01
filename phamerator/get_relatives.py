#!/usr/bin/env python

import db_conf
import phamerator_manage_db
import sys

GeneID = sys.argv[1]
c = db_conf.db_conf().get_cursor()
relatives = phamerator_manage_db.get_relatives(c, GeneID, alignmentType='clustalw', clustalwThreshold=0.275)
for r in relatives:
  print 'query:', r[0], 'subject:', r[1], 'score:', r[2]
