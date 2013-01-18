#!/usr/bin/env python

import urllib2, os, sys, threading, os
import MySQLdb
import getpass

try:
  from phamerator import *
  from phamerator import phamerator_manage_db
  from phamerator.db_conf import db_conf
except:
  sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
  sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
  from phamerator import *
  from phamerator import phamerator_manage_db
  from phamerator import pham
  from phamerator.db_conf import db_conf

class cddSearch:
  def __init__(self,db=None,tempfilepath=None,pathtoblast=None,pathtocddDatabase=None,PhageIDs=None):
    #password = getpass.getpass()
    self.username = raw_input("Database Username: ")
    self.password = getpass.getpass("Database Password: ")
    self.server = raw_input("Database Server: ")
    self.database = raw_input("Database Name: ")
    print 'using databse: %s' % self.database
    self.c = db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    if not PhageIDs:
      PhageIDs = phamerator_manage_db.get_PhageIDs(self.c)
    self.PhageIDs = list(PhageIDs)
    #errorHandler = pham.errorHandler()
    self.dbase = pham.db(self.c)

    if pathtocddDatabase == None:
      self.rpsblast_db = os.path.join(os.environ['HOME'], 'Databases', 'Cdd', 'Cdd')
    else:
      self.rpsblast_db = pathtocddDatabase

    if tempfilepath == None:
      self.query_filename = "/tmp/query.fasta"
    else:
      self.query_filename = tempfilepath


    if pathtoblast == None:
      try:
        import ConfigParser
        cfg = ConfigParser.RawConfigParser()
        cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
        blast_dir = cfg.get('Phamerator','BLAST_dir')
        self.rpsblast_exe = os.path.join(blast_dir,'bin','rpsblast')
        print 'path to rpsblast: %s' % self.rpsblast_exe

      except:
        print "BLAST not found, Exiting"
        sys.exit()

    else:
      self.rpsblast_exe = pathtoblast
    


  def search(self):
    #print 'path to database: %s' % self.rpsblast_db
    fasta = phamerator_manage_db.get_fasta_aa(self.c, self.PhageIDs, include_drafts=True)
    #print fasta
    f = open(self.query_filename,'w')
    f.write(fasta)
    f.close()
    E_VALUE_THRESH = 0.001 #Adjust the expectation cut-off here
    from Bio.Blast import NCBIStandalone
    output_handle, error_handle = NCBIStandalone.rpsblast(self.rpsblast_exe,self.rpsblast_db, self.query_filename, expectation=E_VALUE_THRESH)
    #errors = error_handle.read()
    #if errors: print 'Errors: %s' % errors
    from Bio.Blast import NCBIXML
    for record in NCBIXML.parse(output_handle):
      #We want to ignore any queries with no search results:
      if record.alignments:
	print "QUERY: %s..." % record.query.split(':')[0]
	for align in record.alignments :
	  for hsp in align.hsps :
	    print " %s HSP, e=%f, from position %i to %i" % (align.hit_id,hsp.expect, hsp.query_start, hsp.query_end)
	    print 'inserting into database'
            align.hit_def = align.hit_def.replace("\"", "\'")
	    #self.dbase.insert(table='domain', hit_id=align.hit_id, description=align.hit_def)
	    #self.dbase.insert(table='gene_domain', GeneID=record.query, hit_id=align.hit_id, expect=float(hsp.expect), query_start=int(hsp.query_start), query_end=int(hsp.query_end))
	    try:
              descList = align.hit_def.split(',')
              if len(descList) >= 3:
                DomainID, Name = descList[0], descList[1]
                description = ','.join(descList[2:])
              elif len(descList) == 2:
                DomainID, description = descList[0], descList[1]
                Name = None
              elif len(descList) == 1:
                description = descList[0]
                DomainID, Name = None
              try: DomainID, Name, description = DomainID.strip(), Name.strip(), description.strip()
              except: pass # if DomainID, Name or description are None, strip() raises an objection
              sqlQuery = """insert into domain (hit_id, DomainID, Name, description) VALUES ("%s", "%s", "%s", "%s")""" % (align.hit_id, DomainID, Name, description)
	      self.c.execute(sqlQuery)
	      self.c.execute('COMMIT')
	    except MySQLdb.Error, e:
              print sqlQuery
	      if e[0] == 1062:
		print e
	      else:
                print e
                print 'exiting on error.'
		sys.exit()

            try:
              sqlQuery = """insert into gene_domain (GeneID, hit_id, expect, query_start, query_end) VALUES ("%s", "%s", %s, %s, %s)""" % (record.query.split(':')[1], align.hit_id, float(hsp.expect), int(hsp.query_start), int(hsp.query_end))
	      self.c.execute(sqlQuery)
	      self.c.execute('COMMIT')
	    except MySQLdb.Error, e:
              print sqlQuery
	      if e[0] == 1062:
		print e
	      else:
                print e
                print 'exiting on error.'
		sys.exit()

	    print align.hit_def + "\n"
	    assert hsp.expect <= E_VALUE_THRESH
    print "Done\n"


if __name__ == "__main__":
  if len(sys.argv) == 1:
    print "usage:\ncddSearch.py <path to rpsblast executable> <path to cdd database> <query fastA file path>"
    sys.exit()
  elif len(sys.argv) == 2:
    cdd = cddSearch(PhageIDs=tuple(sys.argv[2].replace(',', ' ').split()))
  elif len(sys.argv) == 4:
    cdd = cddSearch(tempfilepath=sys.argv[4],pathtoblast=sys.argv[2],pathtocddDatabase=sys.argv[3])
  else:
    print "Error, please try again.\n"
    sys.exit()
  cdd.search()



