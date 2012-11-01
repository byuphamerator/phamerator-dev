#!/usr/bin/env python

#import Pyro.core
#import Pyro.naming
import MySQLdb
import time
import random
#import threading
import db_conf
import sys
import pham_comparator

class errorHandler:
  def show_sql_errors(self,c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      print error

class phamBuilder (errorHandler):
  
  def __init__(self, type):
    threshold_score_blast = sys.argv[1]
    threshold_score_clustalw = sys.argv[2]
    db = db_conf.db_conf()
    c = db.get_cursor()
    # dict whose keys are pham names.  Each value is a list of genes that are a member of that particular pham
    self.phams = {}
    try: c.execute("""SELECT GeneID FROM gene""")
    except: self.show_sql_errors(c)
    GeneIDs = c.fetchall()
    # for every gene in the 'gene' table
    
    for GeneID in GeneIDs:
      #time.sleep(1)
      GeneID = GeneID[0]
      added = False
      # get all the alignments for that gene with a good score
      if type == 'clustalw':
        c.execute("""SELECT query, subject FROM query_subject, clustalw WHERE ((query = '%s' OR subject = '%s') AND query_subject.id = clustalw.id AND score >= %s)""" % (GeneID, GeneID, threshold_score_clustalw))
      elif type == 'blast':
        c.execute("""SELECT query, subject FROM query_subject, blast WHERE (query = '%s' OR subject = '%s') AND blast.score <= %s AND blast.id = query_subject.id UNION SELECT query, subject FROM subject_query, blast WHERE (query = '%s' OR subject = '%s') AND blast.score <= %s AND blast.id = subject_query.id""" % (GeneID, GeneID, threshold_score_blast, GeneID, GeneID, threshold_score_blast))
      
      alignments = c.fetchall()
      #print len(alignments), 'genes have a good alignment score with', GeneID
      # for each good alignment
      for alignment in alignments:
        query, subject = alignment
        #print 'query:', query, 'subject:', subject
        #time.sleep(1)
        # look at every pham
        #print 'phams:', self.phams
        for pham in self.phams.keys():
          #time.sleep(1)
          #print 'query:', query, 'subject:', subject, 'GeneID:', GeneID

          if GeneID not in self.phams[pham]:
            # if the 'query' gene is in this pham and is not the current gene, then add the current GeneID (subject)
            if GeneID != query and query in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              #if pham == 1: print 'added', GeneID, 'to pham 1 because query', query, 'in this pham'
              #print 'added', GeneID, 'to pham:', pham
            # if the 'subject' gene is in this pham and is not the current gene, then add the current GeneID (query)
            elif GeneID != subject and subject in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              #if pham == 1: print 'added', GeneID, 'to pham 1 because subject', subject, 'in this pham'
              #print 'added', GeneID, 'to pham:', pham
      if added == False:
        self.phams.keys().sort()
        if len(self.phams) > 0: key = self.phams.keys()[-1:][0] + 1
        else: key = 0
        if self.phams.has_key(key):
          print 'duplicate key error'
          sys.exit()
        self.phams[key] = [GeneID]
        #if key == 1: print 'creating pham 1 for', GeneID
        #print "creating new pham for", GeneID

  def consolidate_phams(self):
    db = db_conf.db_conf()
    c = db.get_cursor()
    try: c.execute("""SELECT GeneID FROM gene""")
    except: self.show_sql_errors(c)
    GeneIDs = c.fetchall()
    # for every gene in the 'gene' table
    for GeneID in GeneIDs:
      #time.sleep(1)
      GeneID = GeneID[0]
      firstPham = None
      tempPhams = self.phams
      for pham in tempPhams.keys():
        if GeneID in tempPhams[pham]:
          if not firstPham:
            firstPham = pham
          else:
            #if pham in (0,1,2,3,4,5): print 'adding genes from pham', pham, 'to pham', firstPham
            for gene in self.phams[pham]:
              self.phams[firstPham].append(gene)
            del self.phams[pham]

pB = phamBuilder('blast')
pB.consolidate_phams()
pC = phamBuilder('clustalw')
pC.consolidate_phams()


print "number of blast phams:", len(pB.phams)
for pham in pB.phams:
  print str(pham) + ':', len(pB.phams[pham])
  output = str(pham)
  for gene in pB.phams[pham]: output = output + ',' + str(gene)
  output = output + '\n'
  print output

print "number of clustalw phams:", len(pC.phams)
for pham in pC.phams:
  print str(pham) + ':', len(pC.phams[pham])
  output = str(pham)
  for gene in pC.phams[pham]: output = output + ',' + str(gene)
  output = output + '\n'
  print output


comparator = pham_comparator.pham_comparator()
comparator.compare_B_to_C(pB, pC)
comparator.compare_C_to_B(pB, pC)

#genes = pB.phams[26]
#db = db_conf.db_conf()
#c = db.get_cursor()

#for gene in genes:
#  c.execute("""SELECT GeneID, name, translation FROM gene WHERE GeneID = '%s'""" % gene)
#  for GeneID, name, translation in c.fetchall():
#    print '>' + name + '(' + GeneID +')\n' + translation

# get a gene
# for each pham
# if the gene not in any phams:
  # put the gene in a new pham
# if the gene has a good score with any member of that pham:
  # add the gene to that pham
