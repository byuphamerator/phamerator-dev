#!/usr/bin/env python

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import getopt, getpass, signal, MySQLdb, re, db_conf, time, string
import ConfigParser

def update_cluster(c, filename):
  '''parse a csv file with cluster info and use it to update the database'''
  f = open(filename).readlines()
  for line in f:
    line = line.strip()
    if line.count('\t') != 1:
      print 'line %s has %s tabs' % (line, line.count('\t'))
      continue
    name, cluster = line.split('\t')
    if cluster.upper() == 'NON':
      cluster = None
    c.execute("select name from phage where name IN ('%s', '%s-DRAFT', '%s_draft', '%s-DRAFT-INC', '%s_draft_inc')"  % (name, name, name, name, name))
    if c.rowcount == 0:
      print '%s not in database' % name
      continue
    #c.execute("select name from phage where name IN ('%s', '%s-DRAFT') and cluster = '%s'"  % (name, name, cluster))
    #if c.rowcount == 1:
    #  print '%s already assigned to a cluster' % name
    #  continue
    #else:
    if cluster:
      c.execute("update phage set cluster = '%s' where name IN ('%s', '%s-DRAFT', '%s_draft', '%s-DRAFT-INC', '%s_draft_inc')" % (cluster, name, name, name, name, name))
    else:
      c.execute("update phage set cluster = NULL where name IN ('%s', '%s-DRAFT', '%s_draft', '%s-DRAFT-INC', '%s_draft_inc')" % (name, name, name, name, name))

    print '%s:%s' % (name, cluster)
  c.execute('commit')

def samesies(c, phages):
  '''look to see whether two phages have the same sequence and same genes'''
  phage1, phage2 = phages.split('_')
  c.execute("select sequence from phage where PhageID IN ('%s', '%s')" % (phage1, phage2))
  result = c.fetchall()
  seqs = []

  for r in result:
    seqs.append(r[0])

  print len(seqs[0]), len(seqs[1])
  print seqs[0] == seqs[1]

  c.execute("select start, stop from gene, phage where gene.PhageID = phage.PhageID and phage.PhageID = '%s' ORDER BY start" % phage1)
  result = c.fetchall()
  genes1 = []

  for r in result:
    genes1.append(r)

  c.execute("select start, stop from gene, phage where gene.PhageID = phage.PhageID and phage.PhageID = '%s' ORDER BY start" % phage2)
  result = c.fetchall()
  genes2 = []

  for r in result:
    genes2.append(r)

  print genes1 == genes2

  for a in range(0, max(len(genes1), len(genes2))):
    if genes1[a] != genes2[a]: print genes1[a], genes2[a]

def usage():
  '''Prints program usage information'''
  print """update_cluster [OPTION] [ARGUMENT]
           -h, --help: print this usage information
           -u, --username: database username
           -p, --password: prompt for a database password
           -s, --server: address of the database server
           -d, --database: name of the database on the server
               --update_cluster: update the cluster info from a csv file
               --samesies: check to see if two phages are the same
           --username, --server, and --database are required. Specify --update_cluster to import a
		.csv file as a cluster specification."""

def main(argv):
  if len(sys.argv) == 1:
    usage()
    sys.exit()
  
  addToDbFromNCBI = []
  addToDbFromFile = []
  removeFromDb = []
  listPhages = False
  try:                                
    opts, args = getopt.getopt(argv, "hlpc:u:t:s:d:i:a:r:e:", ["help", "list", "password", "create=", "username=", "server=", "database=", "import=", "add=", 'remove=', "template=", "clone=", 'refseq=', "update_cluster=", "samesies="])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  if 'server' not in opts: server = 'localhost'
  if 'username' not in opts: username = None
  if 'password' not in opts: password = None
  do_update_cluster = False
  do_samesies = False
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    elif opt in ("-p", "--password"):
      password = getpass.getpass("Password: ")
    elif opt in ("-u", "--username"):
      username = arg
    elif opt in ("-s", "--server"):
      server = arg
    elif opt in ("-d", "--database"):
      database = arg
    elif opt in ("-l", "--list"):
      listPhages = True
    elif opt in ("-i", "--import"):
      addToDbFromFile.append(arg)
    elif opt in ("--update_cluster",):
      do_update_cluster = True
    elif opt in ("--samesies",):
      do_samesies = True
    elif opt in ("-a", "--add"):
      refseq = False
      for o2, a2 in opts:
        if o2 in ("-e", "--refseq"):
          refseq = a2
      addToDbFromNCBI.append((arg, refseq))
      # add phage
    elif opt in ("-r", "--remove"):
      removeFromDb.append(arg)
      # remove phage
    elif opt in ("-c", "--create"):
      database = arg
      clone = None
      template = None
      for o2, a2 in opts:
        if o2 in ("-t", "--template"):
          template = a2
        if o2 in ("--clone",):
          clone = a2
      if clone and template:
        print "--template and --clone are mutually exclusive options"
        sys.exit()
      create_db(template=template, db_name=database, clone=clone)
      sys.exit()
  if not username or not password:
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.my.cnf'))
    try:
      username = cfg.get('client','user')
    except ConfigParser.NoOptionError:
      username = raw_input('database username: ')
    try:
      password = cfg.get('client','password')
    except ConfigParser.NoOptionError:
      password = getpass.getpass('database password: ')
     
  c = db_conf.db_conf(username=username, password=password, server=server, db=database).get_cursor()
  if do_update_cluster: update_cluster(c, arg)
  if do_samesies: samesies(c, arg)
  if listPhages:
    phages = get_phages(c, name='name')
    for phage in phages: print phage

  original_phages = get_phages(c, PhageID='PhageID')

  for item in addToDbFromFile:
    record = parse_GenBank_file(item)
    problems = check_record_for_problems(record)
    if problems:
      #sys.exit()
      a = None
      while not a:
        a = raw_input("Continue (y/N): ")
        if not a: a = 'N'
        if a not in ('Y','y','N','n'): a = None
      if a not in ('Y', 'y'):
        print 'exiting due to the errors printed above\ndatabase is unchanged'
        sys.exit()
    try: PhageID = add_phage(record, c = c)
    except: c.execute("ROLLBACK")
    if PhageID:
      add_genes(record, c = c)
      # don't need to add rows to alignment, clustalw or blast anymore
      #add_alignments(PhageID, c = c)
    else: print 'There was an error adding phage', item, 'to the database.'
    c.execute("COMMIT")
  for item in addToDbFromNCBI:
    queryString, refseq = item
    print "searching GenBank for phage '" + queryString + "'"
    NcbiQuery = query.query(queryString, allowRefSeqs=refseq)
    NcbiQuery.run()
    ###
    feature_parser = GenBank.FeatureParser()
    ncbi_dict = GenBank.NCBIDictionary('nucleotide', 'genbank', parser = feature_parser)
    if len(NcbiQuery.results) > 1:
      selection = -1
      for i in range(len(NcbiQuery.results)):
        print i+1, '\t', ncbi_dict[NcbiQuery.results[i]]
      selection = raw_input("Your search returned multiple results.  Please type the number for your selection: ")
      selection = int(selection) - 1
    else:
      selection = 0
    print 'creating parser...'
    if selection == -1: ## Accounts for non-existent phage query
      print 'non-existent phage query'
      self.result = 0
    else:
      print 'got result'
      result = ncbi_dict[NcbiQuery.results[selection]]
    ###
    if result:
      PhageID = add_phage(result,c=c)
      if PhageID:
        add_genes(result, c = c)
        # don't need to add rows to alignment, clustalw or blast anymore
        #add_alignments(PhageID, c = c)
      else: print 'There was an error adding phage', item, 'to the database.'
      c.execute("COMMIT")
  for item in removeFromDb:
    PhageID = get_PhageID_from_name(c, arg)
    if PhageID:
      print "removing phage '" + item + "' from the database"
      remove_phage_from_db(item, c)
  new_phages = get_phages(c, PhageID='PhageID')

  if phages_have_changed(original_phages, new_phages): reset_blast_table(c)
  
  #  phamPub.publish_db_update("fasta", 'BLAST database is current') if __name__ == '__main__': main(sys.argv[1:])

#  def main():
#    #gtk.main()
#    return 0       

#  if __name__ == "__main__":
#    #TextViewExample()
#    main()

if __name__ == '__main__':
  main(sys.argv[1:])

  

    

