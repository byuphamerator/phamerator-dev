#!/usr/bin/env python

import MySQLdb
import time
import random
import db_conf
import sys, colorsys

# for each gene in the database that's not already in a pham
#   find its relatives
#   for each relative:
#     if it's already in a pham, add the new gene and all relatives to that pham
#     else, create a new pham (without a number) and add that pham to a list of new phams
#   consolidate the new phams, still without giving them numbers
#   consolidate all phams, but any that are joined together get added to pham_history
#   and new phams get an unused name

class nameConverter:
  '''converts a GeneID to a (probably) unique phage+gene name'''
  def __init__(self):
    self.c = db_conf.db_conf().get_cursor()
  def GeneID_to_name(self, GeneID):
    self.c.execute("""SELECT phage.name, gene.name FROM phage, gene WHERE phage.PhageID = gene.PhageID AND GeneID = '%s'""" % GeneID)
    p, g = self.c.fetchone()
    p = p.split(' ')[-1:][0]
    if g.find(p) == -1: n = str(p+'_'+g)
    else: n = str(g)
    return n

class pham:
  '''hold name and members of a pham'''
  def __init__(self, name, genes=None):
    self.name = name
    self.genes = genes

class errorHandler:
  '''prints SQL warning messages'''
  def show_sql_errors(self,c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      print error

class phamBuilder (errorHandler):
  '''builds phams from alignment score generated with blast, clustalw, or both'''
  def __init__(self):
    '''parse command line arguments, setup a python dictionary to hold phams, and create a nameConverter object'''
    db = db_conf.db_conf()
    self.c = db.get_cursor()
    #self.alignmentType = sys.argv[1]
    self.alignmentType = 'clustalw'
    print 'alignment type:', self.alignmentType
    if self.alignmentType == 'clustalw':
      #self.clustalwThreshold = float(sys.argv[2])
      self.clustalwThreshold = 0.275
      print 'clustalw threshold:', self.clustalwThreshold
    elif self.alignmentType == 'blast':
      #self.blastThreshold = float(sys.argv[2])
      self.blastThreshold = 0.0001
      print 'blast threshold:', self.blastThreshold
    elif self.alignmentType == 'both':
      #self.blastThreshold, self.clustalwThreshold = float(sys.argv[2]), float(sys.argv[3])
      self.blastThreshold, self.clustalwThreshold = 0.0001, 0.275
      print 'clustalw threshold:', self.clustalwThreshold
      print 'blast threshold:', self.blastThreshold
    else:
      print 'usage: phamBuilder.py {blast|clustalw|both} [blast_threshold_score] [clustalw_threshold_score]'
      sys.exit()
    # dict whose keys are pham names.  Each value is a list of genes that are a member of that particular pham
    self.phams = {}
    self.nc = nameConverter()
    self.old_phams = []
    self.get_pham_history_names()
    sqlQuery = "SELECT name FROM pham"
    try:
      self.c.execute(sqlQuery)
      results = self.c.fetchall()
      for r in results: self.old_phams = r[0]
    except:
      self.show_sql_errors(self.c)

  def get_phams(self):
    '''get the previously assembled phams and stick them in a dict'''
    sqlQuery = "SELECT name, GeneID FROM pham"
    try:
      self.c.execute(sqlQuery)
      results = self.c.fetchall()
      for r in results:
        name, GeneID = r[0], r[1]
        if self.phams.has_key(name): self.phams[name].append(GeneID)
        else: self.phams[name] = [GeneID]
    except: self.show_sql_errors(self.c)
    
  def construct_phams(self):
    '''first pass at assembling phams'''
    # get genes that are in the gene table but not in the pham table
    sqlQuery = "SELECT gene.GeneID FROM gene LEFT JOIN pham ON gene.GeneID = pham.GeneID WHERE pham.GeneID IS NULL"
    try:
      self.c.execute(sqlQuery)
      results = self.c.fetchall()
      newGenes = []
      for r in results: newGenes.append(r[0])
    except:
      self.c.show_sql_errors(self.c)
    for GeneID in newGenes:
      # only build phams using genes that aren't already in phams
      #if GeneID in self.pham_names: break

      added = False
      # get all the alignments for that gene with a good score
      if self.alignmentType == 'clustalw':
    	# I might not need the "query.type = 'Q' AND subject.type = 'S'" in the next SQL statement
        self.c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s""" % (GeneID, GeneID, self.clustalwThreshold))
      elif self.alignmentType == 'blast':
        self.c.execute("""SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s""" % (GeneID, GeneID, self.blastThreshold))
      elif self.alignmentType == 'both':
        self.c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s UNION SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s""" % (GeneID, GeneID, self.clustalwThreshold, GeneID, GeneID, self.blastThreshold))
      else:
        print 'usage: phamBuilder.py {blast|clustalw} threshold_score'
      alignments = self.c.fetchall()
      #print len(alignments), 'genes have a good alignment score with', GeneID
      # for each good alignment
      for alignment in alignments:
        query, subject, score = alignment
        # look at every pham
        #print 'phams:', self.phams
        for pham in self.phams.keys():
          if GeneID not in self.phams[pham]:
            # if the 'query' gene is in this pham and is not the current gene, then add the current GeneID (subject)
            if GeneID != query and query in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              print 'added', GeneID, 'to pham', pham, 'because', query, 'in this pham (score =', str(score), ')'
              ##print 'added', self.nc.GeneID_to_name(GeneID), 'to pham', pham, 'because query', self.nc.GeneID_to_name(query), 'in this pham. (score = ' + str(score) + ')'

            # if the 'subject' gene is in this pham and is not the current gene, then add the current GeneID (query)
            elif GeneID != subject and subject in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              print 'added', GeneID, 'to pham', pham, 'because', subject, 'in this pham (score =', str(score), ')'
              ##print 'added', self.nc.GeneID_to_name(GeneID), 'to pham', pham, 'because subject', self.nc.GeneID_to_name(subject), 'in this pham. (score = ' + str(score) + ')'

      # creating a new pham, so we need to figure out the lowest available pham number
      if added == False:
        key = self.get_next_avail_pham_name()
        self.phams[key] = [GeneID]
        print 'created pham', key, 'with members:', self.phams[key]
#        for alignment in alignments:
#          query, subject, score = alignment
#          self.phams[key] = [GeneID]
#          if query not in self.phams[key]:
#            self.phams[key].append(query)
#          if subject not in self.phams[key]:
#            self.phams[key].append(subject)

  def renumber_phams(self):
    '''renames phams so that they are numbered consecutively'''
    # for pham in self.phams
    #   check if pham in pham_history
    #   if yes:
    #   check if pham has child
    #   check if pham has parent
    self.get_pham_history_names()
    print 'renumbering phams consecutively...'
    keys = self.phams.keys()
    keys.sort()
    #newkeys = range(1, len(self.phams.keys())+1)
    consec_key = keys[0]
    for key in keys:
      if key not in self.pham_history_names:
        if key != consec_key:
          self.phams[consec_key] = self.phams[key]
          del self.phams[key]
        consec_key += 1

  def get_next_avail_pham_name(self):
    """find the lowest available number that can be safely used as a pham name"""
    keys = self.phams.keys()
    keys.sort()
    if len(self.phams) > 0:
      maxCurrentKey = keys[-1:][0]
      #while key in self.pham_history_names:
        #  print key, 'is in pham_history.  Trying a new key.'
        #  key += 1
    else:
      maxCurrentKey = 0
    sqlQuery = "SELECT MAX(name) FROM pham"
    try:
      self.c.execute(sqlQuery)
      maxPreviousKey = self.c.fetchone()[0]
      if not maxPreviousKey: maxPreviousKey = 0
      #else: key = 1
    except:
      print sqlQuery
      self.show_sql_errors(self.c)
      sys.exit()
    key = max(maxCurrentKey, maxPreviousKey) + 1
    while key in self.pham_history_names:
      print key, 'is in pham_history.  Trying a new key.'
      key += 1
    if self.phams.has_key(key):
      print 'duplicate key error: key =', key
      print self.phams
      sys.exit()
    return key    

  def consolidate_phams(self):
    """join together phams that share a common member"""

    changed = False
    try: self.c.execute("""SELECT GeneID FROM gene""")
    except: self.show_sql_errors(self.c)
    GeneIDs = self.c.fetchall()
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
            ##print 'adding ' + str(len(self.phams[pham])) + ' genes from pham', pham, 'to pham', firstPham, 'because', self.nc.GeneID_to_name(GeneID), 'in both'
            # add all the genes from this pham to the other pham,
            if pham in self.old_phams and firstPham in self.old_phams:
              parent = self.get_next_avail_pham_name()

              # add pham and firstPham to pham_history and get a new key for the new super-pham
              for child in [pham, firstPham]:
                try:
                  sqlQuery = "INSERT INTO pham_history(name, parent) VALUES (%s, %s)" % (child, parent)
                  self.c.execute(sqlQuery)
                except:
                  self.show_sql_errors(self.c)

              for gene in self.phams[pham]:
                if gene not in self.phams[firstPham]:
                  self.phams[firstPham].append(gene)
              # finally, delete this pham
              del self.phams[pham]
              changed = True
    return changed

  def get_mean(self):
    '''reports average number of members in all phams'''
    total_members = 0
    for pham in self.phams.keys():
      total_members = total_members + len(self.phams[pham])
    mean = float(total_members)/len(self.phams.keys())
    print """mean = (float(number of genes)/(number of phams))"""
    print mean, '= ((', total_members, ')/(', len(self.phams.keys()), '))'
    return mean

  def get_number_of_phams_with_length(self, length):
    '''reports the number of phams with the specified number of members'''
    number = 0
    for pham in self.phams.keys():
      if len(self.phams[pham]) == length: number += 1
    return number

  def save_phams(self):
    '''adds pham information to the pham table in the database'''
    #self.reset_pham_table()
    print 'saving', len(self.phams.keys()), 'phams'
    for pham in self.phams.keys():
      for member in self.phams[pham]:
        print 'adding', member, 'to pham', pham, 'row in pham table'
        #print "INSERT INTO pham (name, GeneID) VALUES (%s, '%s')" % (pham, member)
        try:
          sqlQuery = "INSERT INTO pham (name, GeneID) VALUES (%s, '%s')" % (pham, member)
          self.c.execute(sqlQuery)
        except:
          print "error in 'save_phams':", sqlQuery
          self.show_sql_errors(self.c)
          sys.exit()
      try: self.c.execute("COMMIT")
      except: self.show_sql_errors(self.c)
      self.assign_color(pham)

  def assign_color(self, name):
    '''create a random color and return it'''
    h=s=v=0
    while h <= 0: h = random.random()
    while s < 0.5: s = random.random()
    while v < 0.8: v = random.random()
    rgb = colorsys.hsv_to_rgb(h,s,v)
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    hexrgb = '#%02x%02x%02x' % rgb
    try: self.c.execute("INSERT INTO pham_color(name, color) VALUES (%s, '%s')" % (name, hexrgb))
    except:
      print "error in 'assign_color'"
      self.show_sql_errors(self.c)
      sys.exit()
    try: self.c.exexute("COMMIT")
    except: self.show_sql_errors(self.c)

  def get_pham_history_names(self):
    """get all the names from the pham_history table so they can be checked against to ensure we don't reuse them"""
    try: self.c.execute("SELECT name FROM pham_history")
    except:
      print "Error getting pham_history names"
      self.show_sql_errors(self.c)
    r = self.c.fetchall()
    names = []
    for name in r: names.append(r[0])
    self.pham_history_names = names
    print 'pham_history_names:', self.pham_history_names

def main():
  pB = phamBuilder()
  print pB.phams, 'after phamBuilder()'
  pB.construct_phams()
  print pB.phams, 'after construct_phams()'
  while 1:
    changed = pB.consolidate_phams()
    if not changed: break
  print pB.phams, 'after consolidate_phams()'
  pB.renumber_phams()
  print pB.phams, 'after renumber_phams()'
  pB.save_phams()
  print pB.phams, 'after save_phams()'

if __name__ == '__main__':
  main()
