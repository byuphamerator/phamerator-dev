#!/usr/bin/env python

import os, sys, time, socket, getopt, getpass
import Pyro.core
import shutil
import time
import getopt
from Bio.Blast import NCBIStandalone
from Bio.Blast import NCBIXML
#from Bio import Fasta
from types import *

class options:
  def __init__(self, argv):
    try:
      opts, args = getopt.getopt(argv, "hpn:u:a:d:", ["help", "password", "nsname=", "user=", "app-dir=", "data-dir="])
    except getopt.GetoptError:
      print 'error running getopt.getopt'
      self.usage()
    self.argDict = {}
    for opt, arg in opts:
      if opt in ("-h", "--help"):
        self.usage()
        sys.exit()
      elif opt in ("-p", "--password"):
        self.argDict['password'] = getpass.getpass('password: ')
      elif opt in ("-n", "--nsname"):
        self.argDict['nsname'] = arg
      elif opt in ("-u", "--user"):
        self.argDict['user'] = arg
      elif opt in ("-a", "--app-dir"):
        self.argDict['app-dir'] = arg
      elif opt in ("-d", "--data-dir"):
        self.argDict['data-dir'] = arg

    if not self.argDict.has_key('password'): self.argDict['password'] = ''
    required_args = ('nsname', 'user', 'app-dir', 'data-dir')
    for a in required_args:
      if a not in self.argDict:
        print "required argument '%s' is missing" % a
        self.usage()
        sys.exit()

  def usage(self):
    '''Prints program usage information'''
    print """blastclient.py [OPTION] [ARGUMENT]
             -h, --help: print this usage information
             -u, --user=<username>: specify a username on the database
             -p, --password: prompt for a password
             -a, --app-dir: location where BLAST is installed
             -d, --data-dir: location where fasta database should be stored
             -n, --nsname: PYRO NS name, required"""

class blast:
  def __init__(self, blastDataDir='/tmp/BLAST', blastAppDir='~/Applications/BLAST/bin/'):
    if not os.path.isdir(blastDataDir):
      print "data directory '%s' doesn't exist.  creating it..." % blastDataDir
      os.mkdir(blastDataDir)
    print "checking for 'formatdb' in '%s' " % blastDataDir
    if os.path.exists(os.path.join(blastDataDir, 'formatdb')): print 'yes'
    else:
      print 'no'
      shutil.copy(os.path.join(blastAppDir,'formatdb'), blastDataDir)
      print "copying 'formatdb' to '%s'" % blastDataDir
    self.blastDataDir, self.blastAppDir = blastDataDir, blastAppDir
 
  def blast(self):
    '''aligns sequences using blast'''
    blastAppDir = self.blastAppDir
    blastDB = os.path.join(self.blastDataDir, 'blastDB.fasta')
    blastQueryFile = os.path.join(self.blastDataDir, 'filetoblast.txt')
    print 'path to filetoblast.txt:', blastQueryFile
    if sys.platform == 'win32':
      blastall_name = 'Blastall.exe'
    else:
      blastall_name = 'blastall'
    blast_exe = os.path.join(blastAppDir, blastall_name)
    if sys.platform == 'win32':
       import win32api
       blastDB = win32api.GetShortPathName(blast_db)
       blastQueryFile = win32api.GetShortPathName(blastQueryFile)
       blast_exe = win32api.GetShortPathName(blast_exe)
    blast_out, error_info = NCBIStandalone.blastall(blast_exe, 'blastp', blastDB, blastQueryFile, align_view=7)
    #print error_info.read()
    #print blast_out.read()
    blast_records = NCBIXML.parse(blast_out)
    results = []
    recordnumber = 0
    nonmatchingQueries = []
    while 1:
      recordnumber += 1
      try: b_record = blast_records.next()
      except StopIteration: break

      if not b_record:
        continue
      print 'query:', b_record.query
      e_value_thresh = 0.0001
      significant = False
      for alignment in b_record.alignments:
        bestHsp = None
        for hsp in alignment.hsps:
          if not bestHsp: bestHsp = hsp.expect
          elif bestHsp < hsp.expect: continue
          if hsp.expect < e_value_thresh:
            alignment.title = alignment.title.replace(">","")
            #if b_record.query != alignment.title:
            #print 'dir(alignment):', dir(alignment)
            #print 'hsps: ',alignment.hsps, 'accession:', alignment.accession, 'title:', alignment.title, 'length:', alignment.length
            if b_record.query != alignment.accession:
              significant = True
              print 'adding', b_record.query, 'and', alignment.accession, 'to matches (e value: ',hsp.expect, ', bit score: ', hsp.bits, ')'
              results.append((b_record.query, alignment.accession, hsp.expect, hsp.bits))
      print b_record.query, significant
      #if not significant:
      #  print 'adding', b_record.query, 'to the list of queries without matches'
      #  results.append((b_record.query, None, None))
    return results

  def get_blastWorkUnit(self, blastDataDir):
    print 'getting blast work unit...'
    self.blastWorkUnit = self.phamServer.request_seqs(self.client)
    if hasattr(self.blastWorkUnit, 'database'): # Practical test to see if there is work in the work unit
    	self.write_blast_db()
    	self.write_blast_query()
    	return True
    else:
    	return False

  def write_blast_db(self):
    print 'writing work unit to file...'
    f = open(os.path.join(self.blastDataDir, 'blastDB.fasta'), 'w')
    f.write(self.blastWorkUnit.get_as_fasta())
    f.close()
    if sys.platform == 'win32':
      formatdb = 'formatdb.exe '
    else:
      formatdb = 'formatdb'
    os.system(os.path.join(self.blastDataDir, formatdb) + ' -i ' + os.path.join(self.blastDataDir, 'blastDB.fasta -o T'))

  def write_blast_query(self):
    print 'getting query sequence from the server'  
    f = open(os.path.join(self.blastDataDir, 'filetoblast.txt'), 'w')
    f.write('>%s\n%s\n' % (self.blastWorkUnit.query_id, self.blastWorkUnit.query_translation))
    f.close()  

def main(argv):
  opts = options(sys.argv[1:]).argDict
  blaster = blast(blastDataDir=opts['data-dir'], blastAppDir=opts['app-dir'])
  #Pyro.config.PYRO_NS_HOSTNAME='136.142.141.113'
  #Pyro.config.PYRO_NS_HOSTNAME='134.126.95.56'
  if opts['nsname']:
    Pyro.config.PYRO_NS_HOSTNAME=opts['nsname']
  else:
    Pyro.config.PYRO_NS_HOSTNAME='localhost'
  print 'trying to get serverSelector...'
  serverSelector = Pyro.core.getProxyForURI("PYRONAME://serverSelector")
  print 'got serverSelector'
  blaster.client = socket.gethostname()
  print sys.platform, blaster.client
  blaster.server = serverSelector.get_server(sys.platform, blaster.client)
  print 'using server', blaster.server
  blaster.phamServer = Pyro.core.getProxyForURI("PYRONAME://"+blaster.server)

  '''Retrieves sequences to BLAST, BLASTs, and reports scores infinitely'''
  while 1:
    try:
      print 'getting sequences to align'
      if blaster.get_blastWorkUnit(opts['data-dir']):
      	print 'aligning sequences'
      	results = blaster.blast()
      	print 'results:', results
      	blaster.phamServer.report_scores(blaster.blastWorkUnit, results, blaster.client)
      else:
        print 'no work units available...sleeping'
      	time.sleep(30)
    except KeyboardInterrupt:
      blaster.phamServer.disconnect(blaster.client)
      print 'exiting cleanly'
      sys.exit()
if __name__ == '__main__':
  try:
    main(sys.argv[1:])
  except Exception, x:
    print ''.join(Pyro.util.getPyroTraceback(x))
    print 'exiting on pyro traceback'
    sys.exit()

