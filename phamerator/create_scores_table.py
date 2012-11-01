#!/usr/bin/env python

import MySQLdb
import db_conf

c = db_conf.db_conf().get_cursor()
c.execute("""SELECT GeneID FROM gene""")
querys = c.fetchall()
subjects = querys
print 'found', len(querys), 'GeneIDs'
for q in querys:
  query = q[0]
  for s in subjects:
    subject = s[0] 
    if query != subject:
      #try:
      #print """SELECT query, subject FROM scores WHERE query = '%s' AND subject = '%s'""" % (subject, query)
      c.execute("""SELECT query, subject FROM scores WHERE query = '%s' AND subject = '%s'""" % (subject, query))
      result = c.fetchone()
      if result: print result
      #else: print 'no result'
      #except:
        #c.execute("SHOW WARNINGS")
        #errors = c.fetchall()
        #for error in errors:
        #  print error
      if not result:
        try:
          #print """INSERT INTO scores (query, subject) VALUES ( '%s', '%s')""" % (query, subject)
          c.execute("""INSERT INTO scores (query, subject) VALUES ( '%s', '%s')""" % (query, subject))
          c.execute("COMMIT")
        except:
          print 'error'
          c.execute("SHOW WARNINGS")
          errors = c.fetchall()
          for error in errors:
            print error
