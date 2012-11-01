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
  def __init__(self, alignment_type):
    blast_threshold = float(sys.argv[1])
    clustal_threshold = float(sys.argv[2])
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
      if alignment_type == 'clustalw':
        c.execute("""SELECT query, subject, score FROM query_subject, clustalw WHERE ((query = '%s' OR subject = '%s') AND query_subject.id = clustalw.id AND score >= %s)""" % (GeneID, GeneID, clustal_threshold))

      elif alignment_type == 'blast':
        c.execute("""SELECT query, subject, score FROM query_subject, blast WHERE ((query = '%s' OR subject = '%s') AND blast.score <= %s AND blast.id = query_subject.id) UNION SELECT query, subject, score FROM subject_query, blast WHERE ((query = '%s' OR subject = '%s') AND blast.score <= %s AND blast.id = subject_query.id)""" % (GeneID, GeneID, blast_threshold, GeneID, GeneID, blast_threshold))
      else:
        print 'usage: phamBuilder.py {blast|clustalw} threshold_score'
      alignments = c.fetchall()
      #print len(alignments), 'genes have a good alignment score with', GeneID
      # for each good alignment
      for alignment in alignments:
        query, subject, score = alignment
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
             # if pham == 12: print 'added', GeneID, 'to pham 12 because query', query, 'in this pham. (score = ' + str(score) + ')'
              #print 'added', GeneID, 'to pham:', pham
            # if the 'subject' gene is in this pham and is not the current gene, then add the current GeneID (query)
            elif GeneID != subject and subject in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
            #  if pham == 12: print 'added', GeneID, 'to pham 12 because subject', subject, 'in this pham. (score = ' + str(score) + ')'
              #print 'added', GeneID, 'to pham:', pham
      if added == False:
        self.phams.keys().sort()
        if len(self.phams) > 0: key = self.phams.keys()[-1:][0] + 1
        else: key = 0
        if self.phams.has_key(key):
          print 'duplicate key error'
          sys.exit()
        #if key == 12: print 'adding', GeneID, 'as the founding member of pham 12'
        self.phams[key] = [GeneID]
        #if key == 1: print 'creating pham 1 for', GeneID
        #print "creating new pham for", GeneID

  def consolidate_phams(self):
    changed = False
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
      # for each pham
      for pham in tempPhams.keys():
        # if the current gene is in this pham
        if GeneID in tempPhams[pham]:
          # and not yet found in any other pham
          if not firstPham:
            # remember that this gene first appeared in this pham
            firstPham = pham
          # if this gene is in a different pham
          else:
            #if firstPham == 12: print 'adding ' + str(len(self.phams[pham])) + ' genes from pham', pham, 'to pham', firstPham, 'because', GeneID, 'in both'
            # add all the genes from this pham to the other pham,
            for gene in self.phams[pham]:
              if gene not in self.phams[firstPham]:
                self.phams[firstPham].append(gene)
            # finally, delete this pham
            del self.phams[pham]
            changed = True
    return changed

pB = phamBuilder('blast')
c = db_conf.db_conf().get_cursor()
while 1:
  changed = pB.consolidate_phams()
  if not changed: break

pC = phamBuilder('clustalw')
while 1: 
  changed = pC.consolidate_phams()
  if not changed: break

comparator = pham_comparator.pham_comparator()
if sys.argv[3] == 'cc':
	comparator.compare(pC, pC, sys.argv[3])
elif sys.argv[3] == 'bb':
	comparator.compare(pB, pB, sys.argv[3])
elif sys.argv[3] == 'bc':
	comparator.compare(pB, pC, sys.argv[3])
elif sys.argv[3] == 'cb':
	comparator.compare(pC, pB, sys.argv[3])
'''print "number of phams:", len(pB.phams)
for pham in pB.phams:
  print str(pham) + ':', len(pB.phams[pham])
  output = ''
  for gene in pB.phams[pham]:
    #c.execute("""SELECT phage.name, gene.name FROM phage, gene WHERE phage.PhageID = gene.PhageID AND GeneID = '%s'""" % gene)
    #p, g = c.fetchone()
    #p = p.split(' ')[-1:][0]
    #if g.find(p) == -1: n = str(p+'_'+g)
    #else: n = str(g)
    #if output: output = output + ',' + n
    #else: output = n
    if output: output = output + ',' + str(gene)
    else: output = str(gene)
  output = output + '\n'
  print output'''

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
