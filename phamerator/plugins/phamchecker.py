#!/usr/bin/env python

try:
  from phamerator import *
  from phamerator.phamerator_manage_db import *
  from phamerator.db_conf import db_conf
  import sys
except:
  import sys, os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
  sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
  from phamerator import *
  from phamerator.phamerator_manage_db import *
  from phamerator.db_conf import db_conf


#def get_all_pham_names(self, c):
def get_all_pham_names(c):
  results = c.execute('SELECT DISTINCT name from pham ORDER BY name')
  phams = []
  [phams.append(int(r[0])) for r in c.fetchall()]
  return phams

def get_pham_members(c, phamName):
  results = c.execute("SELECT GeneID from pham WHERE name = '%s' ORDER BY GeneID" % str(phamName)) 
  # the genes in the 'genes' list are those that are in a particular pham, according to the db
  genes = []
  [genes.append(str(r[0])) for r in c.fetchall()]
  return genes

def get_blast_relatives(c, GeneID, threshold=float(1e-4)):
  if not threshold: return []
  c.execute("SELECT query, subject from scores_summary WHERE blast_score <= %s AND (query = '%s' OR subject = '%s')" % (threshold, GeneID, GeneID))
  results = c.fetchall()
  blastResults = []
  for r in results:
    for i in (r[0], r[1]):
      if i not in blastResults: blastResults.append(i)
  return blastResults

def get_clustalw_relatives(c, GeneID, threshold=0.275):
  #c.execute("SELECT query, subject from scores_summary WHERE clustalw_score >= 0.275 AND (query = '%s' OR subject = '%s')" % (GeneID, GeneID))
  sqlQuery = "SELECT query, subject from scores_summary WHERE clustalw_score >= %s AND (query = '%s' OR subject = '%s')" % (threshold, GeneID, GeneID)
  try:
    c.execute(sqlQuery)
  except:
    print sqlQuery
  results = c.fetchall()
  clustalwResults = []
  for r in results:
    for i in (r[0], r[1]):
      if i not in clustalwResults: clustalwResults.append(i)
  return clustalwResults

def get_all_relatives(c, GeneID, cthreshold, bthreshold):
  relatives = [GeneID,]
  br = get_blast_relatives(c, GeneID, threshold=bthreshold)
  cr = get_clustalw_relatives(c, GeneID, threshold=cthreshold)
  for g in br:
    if g not in relatives: relatives.append(g)
  for g in cr:
    if g not in relatives: relatives.append(g)
  return relatives

# def follow_rel_chain(GeneID, 

def follow_rel_chain(c, GeneID, relatives, ignore=[]):
  # if ignore is set, don't allow this GeneID to pull in relatives
  # this is useful for seeing if a pham is still valid after deleting
  # a genome that contains a member of the pham
  i = relatives
  new = get_all_relatives(c, GeneID, 0.325, None)
  for g in ignore:
    if g in new: new.remove(g)
  for g in new:
    if g not in relatives:
      relatives.append(g)
      relatives = follow_rel_chain(c, g, relatives, ignore=ignore)
    # these next two lines wouldn't do anything!
    #if len(i) != len(relatives):
    #  continue
  #print 'GeneID: %s, relatives: %s' % (GeneID, relatives)
  return relatives

def follow_rel_chain2(c, GeneID, relatives, ignore=[], cthreshold=None, bthreshold=None):
  # if ignore is set, don't allow this GeneID to pull in relatives
  # this is useful for seeing if a pham is still valid after deleting
  # a genome that contains a member of the pham
  relatives = set(relatives)
  new = set(get_all_relatives(c, GeneID, cthreshold, bthreshold))
  #new = set(get_clustalw_relatives(c, GeneID, threshold))
  ignore = set(ignore)
  new = new - ignore - relatives
  relatives = relatives | new
  for g in new:
    relatives = follow_rel_chain2(c, g, relatives, ignore=ignore, cthreshold=cthreshold, bthreshold=bthreshold)
  return list(relatives)

# for a given GeneID
#   newList = []
#   find relatives and add to list
#   for each GeneID in relative list:
#     call this function


def main():
  cfg = ConfigParser.RawConfigParser()
  cfg.read(os.path.join(os.environ['HOME'], '.my.cnf'))
  import sys
  db = sys.argv[1]
  try:
    username = cfg.get('client','user')
  except ConfigParser.NoOptionError:
    username = raw_input('database username: ')
  try:
    password = cfg.get('client','password')
  except ConfigParser.NoOptionError:
    import getpass
    password = getpass.getpass('database password: ')

  c = db_conf(username='root', password=password, server='localhost', db=db).get_cursor()
  phams = get_all_pham_names(c)
  for phamName in phams:
    print phamName
    phamMembers = get_pham_members(c, phamName)
    #for phamMember in phamMembers:
    #  relatives = [phamMember]
    #  #relatives = get_all_relatives(c, phamMember)
    #  #print 'seed: %s' % phamMember
    #  relatives = list(set(relatives) | set(follow_rel_chain2(c, phamMember, relatives)))
    phamMember = phamMembers[0]
    relatives = [phamMember]
    #  #relatives = get_all_relatives(c, phamMember)
    #  #print 'seed: %s' % phamMember
    relatives = list(set(relatives) | set(follow_rel_chain2(c, phamMember, relatives, cthreshold=0.325, bthreshold=1e-50)))


    phamMembers.sort()
    relatives.sort()
    if relatives != phamMembers:
      print '%s cannot account for all genes in pham %s' % (phamMember, phamName)
      print 'relatives: %s\nphamMembers: %s' % (relatives, phamMembers)
      print '%s : %s : %s' % (phamName, phamMembers, relatives)
      print 'mercifully exiting after one mismatch'
      sys.exit()
  print '%s database is OK' % db

if __name__ == '__main__':
  main()

"""  for relative in relatives:
    br = get_blast_relatives(c, phamMembers[0])
    cr = get_clustalw_relatives(c, phamMembers[0])
    for r in br, cr:
      for relative in r:
        if relative not in chain:
          chain.append(relative)
  phamMembers.sort()
  relatives.sort()
  if phamMembers != relatives:
    print '%s : %s : %s' % (phamName, phamMembers, relatives)
"""
