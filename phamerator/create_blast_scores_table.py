#!/usr/bin/env python

import MySQLdb
import db_conf

c = db_conf.db_conf().get_cursor()
c.execute("""SELECT GeneID FROM gene""")
querys = c.fetchall()
subjects = querys
for q in querys:
  query = q[0]
  for s in subjects:
    subject = s[0] 
    if query != subject:
      try:
        c.execute("""INSERT INTO blast_scores (query, subject) VALUES ( '%s', '%s')""" % (query, subject))
      except:
        c.execute("SHOW WARNINGS")
        errors = c.fetchall()
        for error in errors:
          print error
