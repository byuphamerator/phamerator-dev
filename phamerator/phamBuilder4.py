#!/usr/bin/env python

import getopt, getpass, sys, string, time, pham
from phamerator_manage_db import *
from plugins import phamchecker
from plugins.phamchecker import *
import db_conf

def usage():
  '''Prints program usage information'''
  print """phamBuilder4.py [OPTION] [ARGUMENT]
           -h, --help: print this usage information
           -p, --password: prompt for database password
           -u, --user: database username, required
           -s, --server=<server name>: specify the address of the server where the database is located
           -d, --database=<database name>: specify the name of the database to access
           -c, --clustalw_threshold=<threshold value (0-1)>: specify a % identity as a number 0-1
           -b, --blast_threshold=<BLAST E-value>: specify an E-value such as 1e-4"""

def get_options(argv):
  try:
    opts, args = getopt.getopt(argv, "hpu:s:d:c:b:", ["help", "password" "user=",  "server=", "database=", "clustalw_threshold=", "blast_threshold="])
  except getopt.GetoptError:
    usage()
  argDict = {}
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    elif opt in ("-p", "--password"):
      argDict['password'] = True
    elif opt in ("-u", "--user"):
      argDict['user'] = arg
    elif opt in ("-s", "--server"):
      argDict['server'] = arg
    elif opt in ("-d", "--database"):
      argDict['database'] = arg
    elif opt in ("-c", "--clustalw_threshold"):
      argDict['clustalw_threshold'] = float(arg)
    elif opt in ("-b", "--blast_threshold"):
      argDict['blast_threshold'] = float(arg)
  required_args = ('user', 'server', 'database', 'clustalw_threshold', 'blast_threshold')
  for a in required_args:
    if a not in argDict:
      print "required argument '%s' is missing" % a
      usage()
      sys.exit()
  return argDict

def main():
  argDict = get_options(sys.argv[1:])
#  cfg = ConfigParser.RawConfigParser()
#  cfg.read(os.path.join(os.environ['HOME'], '.my.cnf'))
#  try:
#    username = cfg.get('client','user')
#  except ConfigParser.NoOptionError:
  if argDict['user']:
    username = argDict['user']
  else:
    username = raw_input('database username: ')
#  try:
#    password = cfg.get('client','password')
#  except ConfigParser.NoOptionError:
  if "password" in argDict:
    password = getpass.getpass('database password: ')

  database = argDict['database']
  server = argDict['server']
  cthreshold = argDict['clustalw_threshold']
  bthreshold = argDict['blast_threshold']
  c = db_conf.db_conf(username=username, password=password, server=server, db=database).get_cursor()
  db = pham.db(c)
  GeneIDs = get_GeneIDs(c)

  # get all the phams that are in the database
  oldController = pham.PhamController(c, source='db')

  # create an empty PhamController object that will be populated with phams for pre-existing genes only
  # this checks to make sure these phams are still valid based on new BLAST scores
  currentController = pham.PhamController(c)
  new_genes = []
  for GeneID in GeneIDs:
    if not oldController.find_phams_with_gene(str(GeneID)):
      #print '%s is not in a pham' % str(GeneID)
      new_genes.append(str(GeneID))

  print 'there are %s genes that are not assigned to a pham' % len(new_genes)
  print 'ignoring these and verifying the old phams...'

  # Make sure that the existing phams in the database are still valid based on the 
  # current alignment scores

  for GeneID in GeneIDs:
    if GeneID in new_genes: continue
    relatives = follow_rel_chain2(c, GeneID, [], ignore=new_genes, cthreshold=cthreshold, bthreshold=bthreshold)
    p = pham.Pham(name=None, members=[], children=[])
    p.add_members((GeneID,))
    p.add_members(relatives)
    print 'created pham'
    try:
      #print 'creating a new pham and adding it to the currentController:', p
      currentController.add_pham(p)
    except pham.DuplicatePhamError:
      pass
      #print 'pham %s is already in the current controller:' % p

  # Look for phams that should be joined because they each contain the same gene.
  # Join any that are found.

  for GeneID in GeneIDs:
    pwg = currentController.find_phams_with_gene(str(GeneID)) #pwg = phams with gene
    #print 'GeneID: %s, pwg: %s' % (GeneID, pwg)
    if pwg:
      # one (and only one) pham already contains this gene, don't do anything
      if len(pwg) == 1:
	p = pwg[0] 

      # if this gene is already in more than one pham, join those phams
      elif len(pwg) > 1: 
	p = currentController.join_phams(pwg)

  print "there are %s total phams when ignoring new genes" % len(currentController.phams)
  currentController = currentController - oldController
  print "there are %s split phams that need to be phixed" % len(currentController.phams)
  currentController.save()

  # create an empty PhamController object that will be populated with phams for new and pre-existing genes
  # the pre-existing phams will be subtracted out of this object's pham list
  newController = pham.PhamController(c)
  oldController = pham.PhamController(c, source='db')

  # for every gene in the database, figure out if it is already in a pham
  for GeneID in GeneIDs:
    append=True
    relatives = follow_rel_chain2(c, GeneID, [], cthreshold=cthreshold, bthreshold=bthreshold)
    pwg = newController.find_phams_with_gene(str(GeneID)) #pwg = phams with gene
    #print 'GeneID: %s, pwg: %s' % (GeneID, pwg)
    if pwg:
      # one (and only one) pham already contains this gene, don't do anything
      if len(pwg) == 1:
        p = pwg[0] 

      # if this gene is already in more than one pham, join those phams
      elif len(pwg) > 1: 
        ###print 'joining phams...'
        #for item in pwg: print item.members
        p = newController.join_phams(pwg)

    # if this gene isn't in a pham already, create a new pham
    else:
      p = pham.Pham(name=None, members=[], children=[])
      p.add_members((GeneID,))

    # add any genes related to this gene to the pham that it's in
    p.add_members(relatives)

    toJoin = [p]
    for gene in p.members:
      for result in newController.find_phams_with_gene(gene):
        if result not in toJoin: toJoin.append(result)
    if len(toJoin) > 1:
      #print 'joining phams with these members:'
      #for j in toJoin: print j, j.name, j.members
      p = newController.join_phams(toJoin)

    if append:
      ###print 'adding pham', p, 'with members:', p.members
      try: newController.add_pham(p)
      except: pham.DuplicatePhamError
  newController = newController - oldController
  print "there are", len(newController.phams), "new phams."
  for newPham in newController.phams: print newPham
  print "Saving..."
  newController.save()
if __name__ == '__main__':
  main()
