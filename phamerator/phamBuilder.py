#!/usr/bin/env python

import MySQLdb
import time
import random
import db_conf
import sys, colorsys

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
    self.alignmentType = 'both'
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
  def reset_pham_table(self):
    '''removes all pham entries from the 'pham table in the database'''
    try: self.c.execute("TRUNCATE TABLE pham")
    except: self.show_sql_errors(self.c)

  def create_temp_pham_table(self):
    '''creates a temporary mysql table to hold new pham assignments before integrating them with old ones'''
    sqlQuery = '''CREATE TEMPORARY TABLE pham_temp  ( `GeneID` varchar(15) NOT NULL, `name` int(10) unsigned NOT NULL, `color` char(7) default NULL, PRIMARY KEY  (`GeneID`), KEY `name_index` (`name`), CONSTRAINT `pham_ibfk_1` FOREIGN KEY (`GeneID`) REFERENCES `gene` (`GeneID`)) ENGINE=MEMORY'''
    try: self.c.execute(sqlQuery)
    except:
      print "Error creating temporary pham table"
      self.show_sql_errors(self.c)
      
  def get_pham_history_names(self):
    """"get all the names from the pham_history table so they can be checked against to ensure we don't reuse them"""
    try: self.c.execute("SELECT name FROM pham_history")
    except:
      print "Error getting pham_history names"
      self.show_sql_errors(self.c)
    r = self.c.fetchall()
    names = []
    for name in r: names.append(r[0])
    self.pham_history_names = names
    print 'pham_history_names:', self.pham_history_names

  def construct_phams(self):
    '''first pass at building phams by iterating through every gene in the database and looking for others with good alignment scores'''
    self.get_pham_history_names()
    try: self.c.execute("""SELECT GeneID FROM gene""")
    except: self.show_sql_errors(self.c)
    GeneIDs = self.c.fetchall()
    # for every gene in the 'gene' table
    for GeneID in GeneIDs:
      #time.sleep(1)
      GeneID = GeneID[0]
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
          #time.sleep(1)
          #print 'query:', query, 'subject:', subject, 'GeneID:', GeneID
          if GeneID not in self.phams[pham]:
            # if the 'query' gene is in this pham and is not the current gene, then add the current GeneID (subject)
            if GeneID != query and query in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              ##print 'added', self.nc.GeneID_to_name(GeneID), 'to pham', pham, 'because query', self.nc.GeneID_to_name(query), 'in this pham. (score = ' + str(score) + ')'
              #print 'added', GeneID, 'to pham:', pham
            # if the 'subject' gene is in this pham and is not the current gene, then add the current GeneID (query)
            elif GeneID != subject and subject in self.phams[pham]:
              self.phams[pham].append(GeneID)
              added = True
              ##print 'added', self.nc.GeneID_to_name(GeneID), 'to pham', pham, 'because subject', self.nc.GeneID_to_name(subject), 'in this pham. (score = ' + str(score) + ')'
              #print 'added', GeneID, 'to pham:', pham
      if added == False:
        keys = self.phams.keys()
        keys.sort()
        #print 'keys:', self.phams.keys()
        if len(self.phams) > 0:
          key = keys[-1:][0] + 1
          while key in self.pham_history_names:
            print key, 'is in pham_history.  Trying a new key.'
            key += 1
        else:
          sqlQuery = "SELECT MAX(name) FROM pham"
          try:
            self.c.execute(sqlQuery)
            max = self.c.fetchone()[0]
            if max: key = max + 1
            else: key = 1
            while key in self.pham_history_names:
              print key, 'is in pham_history.  Trying a new key.'
              key += 1
          except:
            print sqlQuery
            self.show_sql_errors(self.c)
            sys.exit()
        if self.phams.has_key(key):
          print 'duplicate key error: key =', key
          print self.phams
          sys.exit()
        ##print 'adding', self.nc.GeneID_to_name(GeneID), 'as the founding member of pham', key
        self.phams[key] = [GeneID]
        #if key == 1: print 'creating pham 1 for', GeneID
        #print "creating new pham for", GeneID

  def consolidate_phams(self):
    """join together phams that share a common member"""

    changed = False
    db = db_conf.db_conf()
    c = db.get_cursor()
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
            for gene in self.phams[pham]:
              if gene not in self.phams[firstPham]:
                self.phams[firstPham].append(gene)
            # finally, delete this pham
            del self.phams[pham]
            changed = True
    return changed

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

    consec_key = 1
    for key in keys:
      if key not in self.pham_history_names:
        if key != consec_key:
          self.phams[consec_key] = self.phams[key]
          del self.phams[key]
        consec_key += 1

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
    self.reset_pham_table()
    print 'saving', len(self.phams.keys()), 'phams'
    for pham in self.phams.keys():
      for member in self.phams[pham]:
        ##print 'adding', member, 'to pham', pham, 'row in pham table'
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

  def look_for_parents(self):
    '''looks to see if any of the new phams contain all the members from two or more preexisting phams'''
    ##print self.phams
    relatives = {}
    sqlQuery = "SELECT name, GeneID FROM pham"
    self.c.execute(sqlQuery)
    results = self.c.fetchall()
    # put the old phams in a {} where the keys are pham numbers and the values are a list of GeneIDs
    old_phams = {}
    new_phams = self.phams.copy()
    for name, GeneID in results:
      if not old_phams.has_key(name): old_phams[int(name)] = [GeneID]
      else: old_phams[int(name)].append(GeneID)
    print 'old_phams:', old_phams
    for new_name in self.phams.keys():
      for old_name in old_phams.keys():
        # if the old pham is identical to the new one, the old pham is not a child
        self.phams[new_name].sort()
        old_phams[old_name].sort()
        if self.phams[new_name] == old_phams[old_name]:
          new_phams[old_name] = self.phams[new_name]
          #del new_phams[new_name]
          break
        for old_gene in old_phams[old_name]:
          if old_gene in self.phams[new_name]:
            #print 'renaming', new_name, self.phams[new_name], 'to', old_name, old_phams[old_name]
            #new_phams[old_name] = self.phams[new_name]
            #del new_phams[new_name]
            # this old pham "old_name" is now in "new_name" so remember this and check for more
            if relatives.has_key(new_name): relatives[new_name].append(old_name)
            else: relatives[new_name] = [old_name]
            break

    for parent in relatives.keys():
      # should never happen
      if len(relatives[parent]) < 1: break
      # an old pham has grown
      elif len(relatives[parent]) == 1:
        child = new_phams[parent][0]
        new_phams[child] = new_phams[parent]
        del new_phams[parent]
        break
      # a new pham ate 2 or more old phams
      for child in relatives[parent]:  
        sqlQuery = "INSERT INTO pham_history(name, parent) VALUES (%s, %s)" % (child, parent)
        print old_name, "is a child of", new_name
        try: self.c.execute(sqlQuery)
        except:
          print "error in 'look_for_parents'"
          print sqlQuery
          self.show_sql_errors(self.c)
          sys.exit()
        sqlQuery = "DELETE FROM pham WHERE name = %s" % old_name
        try: self.c.execute(sqlQuery)
        except:
          print "error in look_for_parents"
          print sqlQuery
          self.show_sql_errors(self.c)
          sys.exit()
        del old_phams[old_name]
        print 'deleting', old_name, 'from pham table and dictionary'
        try: self.c.execute("COMMIT")
        except: self.c.show_sql_errors(self.c)
    self.phams = new_phams.copy() # + old_phams.copy()
    print self.phams

    #for new_name in self.phams.keys():
    #  for new_gene in self.phams[new_name]:
    #    sqlQuery = "INSERT INTO pham (name, GeneID) VALUES (%s, '%s')" % (new_name, new_gene)
    #    try: self.c.execute(sqlQuery)
    #    except:
    #      print 'ERROR:', sqlQuery
    #      self.show_sql_errors(self.c)

def main():
  pB = phamBuilder()
  #pB.reset_pham_table()
  pB.create_temp_pham_table()
  pB.construct_phams()
  c = db_conf.db_conf().get_cursor()
  nc = nameConverter()
  while 1:
    print 'consolidating phams...'
    changed = pB.consolidate_phams()
    if not changed: break
  print 'done'
  pB.renumber_phams()
  pB.look_for_parents()
  pB.save_phams()
  print "number of phams:", len(pB.phams)
  print 'mean pham size:', pB.get_mean()
  for pham in pB.phams:
    print str(pham) + ':', len(pB.phams[pham])
    output = ''
    for gene in pB.phams[pham]:
      n =nc.GeneID_to_name(gene)
      if output: output = output + ',' + n
      else: output = n
    output = output + '\n'
    print output

  for i in range(1, 2000):
    n = pB.get_number_of_phams_with_length(i)
    if n:
      print i,':', n

if __name__ == '__main__':
  main()

#import string, re
#m = []
#p = re.compile('g?p\d*')
#pham13 = open('pham13.fasta', 'w')
#for gene in pB.phams[13]:
#  n = nc.GeneID_to_name(gene)
#  try:
#    phageName, geneName = n.split('_')
#    geneName = geneName.split('p')[-1]
#  except:
#    geneName = string.join(p.findall(n)[-1:]).split('p')[-1]
#    phageName = string.join(n.split('p')[:-1], 'p')
#    #phageName = phageName.replace(geneName, '')
#  geneName = 'gp' + geneName
#  m.append((phageName, geneName))
#  pham13.write('>' + phageName + '_' + geneName + '\n')
#  c.execute("SELECT translation FROM gene WHERE GeneID = '%s'" % gene)
#  trans = c.fetchone()[0]
#  pham13.write(trans + '\n')

#for t in m:
#  print t[0] + ' ' + t[1]

#pham13.close()


# get a gene
# if the gene not in any phams:
#   put the gene in a new pham
# else:
#   for each pham
#     if the gene has a good score with any member of that pham:
#       add the gene to that pham
#
#
#
#
#
#
#
#
#
