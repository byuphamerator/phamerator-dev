#!/usr/bin/env python

import getpass
import db_conf
from phamerator_manage_db import *

password = getpass.getpass("enter root database password: ")

c = db_conf.db_conf(username='root', password=password, server='djs-bio.bio.pitt.edu', db='Hatfull').get_cursor()

PhageIDs = get_PhageIDs(c)
#PhageIDs = [get_PhageID_from_name(c, 'L5')]
#print "PhageIDs:", PhageIDs

for PhageID in PhageIDs:
  phageName = get_phage_name_from_PhageID(c, PhageID)
  #if phageName.find('BPs') == -1: break
  GeneIDs = get_GeneIDs(c, PhageID=PhageID)
  genes = {}
  for GeneID in GeneIDs:
    number = get_gene_number_from_GeneID(c, GeneID)
    genes[number] = GeneID
  keys = genes.keys()
  keys.sort()
  #print keys
  #print genes
  for number in keys:
    n2 = number + 2
    GeneID1 = genes[number]
    #print 'n:', n, 'GeneID:', GeneID
    gene1Pham = get_pham_from_GeneID(c, GeneID1)
    try:
      GeneID3 = genes[n2]
      #print 'trying %s (%s) and %s (%s)' % (number, GeneID1, n2, GeneID2)
      gene3Pham = get_pham_from_GeneID(c, GeneID3)
    except KeyError:
      #print 'phage %s has no gene %s' % (phageName, n2)
      continue
    if gene1Pham == gene3Pham:
      gene1Name = get_gene_name_from_GeneID(c, GeneID1)
      GeneID2 = genes[number+1]
      gene2Name = get_gene_name_from_GeneID(c, GeneID2)
      gene2Pham = get_pham_from_GeneID(c, GeneID2)
      gene3Name = get_gene_name_from_GeneID(c, GeneID3)
      if gene2Pham != gene1Pham: print 'Phage: %s: %s (pham%s), %s (pham%s), %s (pham%s)' % (phageName, number, gene1Pham, number+1, gene2Pham, n2, gene3Pham)
