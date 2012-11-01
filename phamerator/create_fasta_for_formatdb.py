#!/usr/bin/env python

import sys
import MySQLdb
import getpass

password = getpass.getpass('password:')

f = open(sys.argv[1], 'w')

db = MySQLdb.connect(user='root', passwd=password, db="pham")
c = db.cursor()
c.execute("""SELECT GeneID FROM gene""")
querys = c.fetchall()

for q in querys:
  query = q[0]
  c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % (query))
  seq = c.fetchone()[0]
  f.write('>' + query + '\n' + seq + '\n')

f.close()
