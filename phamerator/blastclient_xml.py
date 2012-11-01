#!/usr/bin/env python

import os, sys, time, socket
import Pyro.core
import shutil
import time
#from Bio.Clustalw import MultipleAlignCL
from Bio.Blast import NCBIXML
from Bio.Blast import NCBIStandalone
from Bio import Fasta
from types import *

Pyro.config.PYRO_NS_HOSTNAME='djs-bio.bio.pitt.edu'
serverSelector = Pyro.core.getProxyForURI("PYRONAME://serverSelector")
print 'got serverSelector'
client = socket.gethostname()
print sys.platform, client
server = serverSelector.get_server(sys.platform, client)
print 'using server', server
phamServer = Pyro.core.getProxyForURI("PYRONAME://"+server)

def blast(blastRootDirectory):
  if sys.platform == 'win32':
    blast_db = os.path.join(blastRootDirectory, 'blastDB.fasta')
  else:
    if not os.path.isdir('/tmp/BLAST'):
      print "making directory '/tmp/BLAST'"
      os.mkdir('/tmp/BLAST/')
    if not os.path.exists('/tmp/BLAST/formatdb'):
      shutil.copy(os.path.join(blastRootDirectory,'formatdb'), '/tmp/BLAST')
      print "copying 'formatdb' to '/tmp/BLAST/'"
    blast_db = os.path.join('/tmp/BLAST', 'blastDB.fasta')
  #print 'path to blastDB.fasta:', blast_db
  
  blast_file = os.path.join(blastRootDirectory, 'filetoblast.txt')
  #print 'path to filetoblast.txt:', blast_file
  
  if sys.platform == 'win32':
    blastall_name = 'Blastall.exe'
    blast_exe = os.path.join(blastRootDirectory, blastall_name)
  else:
    blastall_name = 'blastall'
    blast_exe = os.path.join(os.getcwd(), '../../BLAST/bin/', blastall_name)

  #print 'path to blastall:', blast_exe
  
  if sys.platform == 'win32':
     import win32api
     blast_db = win32api.GetShortPathName(blast_db)
     blast_file = win32api.GetShortPathName(blast_file)
     blast_exe = win32api.GetShortPathName(blast_exe)
  
  #cont = raw_input('blah')
  #try: 
  blast_out, error_info = NCBIStandalone.blastall(blast_exe, 'blastp', blast_db, blast_file,  align_view=7)
  #except:
  #  f = open(blast_file, 'r')
  #  s = file.read()
  #  print s
  
  #print 'done BLASTing'
  
  print 'errors:', error_info.read()
  print 'blast output:', blast_out.read()
  
  b_parser = NCBIXML.BlastParser()
  #print 'got parser'
  
  b_record = b_parser.parse(blast_out)
  b_iterator = NCBIStandalone.Iterator(blast_out, b_parser)
  #print 'got iterator'
  results = []
  recordnumber = 0
  nonmatchingQueries = []
  while 1:
    recordnumber += 1
    b_record = b_iterator.next()
    
    if not b_record: break
    print 'query:', b_record.query
    if b_record is None:
      break
    e_value_thresh = 0.001
    print 'number of alignments:', len(b_record.alignments)
    significant = False
    for alignment in b_record.alignments:
      for hsp in alignment.hsps:
        if hsp.expect < e_value_thresh:
          alignment.title = alignment.title.replace(">","")
          if b_record.query != alignment.title:
            significant = True
            print 'adding', b_record.query, 'and', alignment.title, 'to the list of matches'
            results.append((b_record.query, alignment.title, hsp.expect))
    print b_record.query, significant
    if not significant:
      print 'adding', b_record.query, 'to the list of queries without matches'
      nonmatchingQueries.append(b_record.query)

  return nonmatchingQueries, results

def create_hex_digest(dictionary):
  import md5
  hash = md5.new()
  hash.update(dictionary['data'])
  digest = hash.hexdigest()
  return digest

def check_db(dictionary_db, blastRootDirectory):
  
  #if not dictionary_db:
  hexDi = create_hex_digest(dictionary_db)
  #else:
  #  hexDi = "1"
  
  if not phamServer.check_if_current_db(hexDi):
    print 'database on the server has changed.  Updating...'
    dictionary_db = phamServer.get_latest_db()
  
    f = open(os.path.join(blastRootDirectory, 'blastDB.fasta'), 'w')
    f.write(dictionary_db['data'])
    f.close()
    if sys.platform == 'win32':
      formatdb = 'formatdb.exe '
    else:
      formatdb = 'formatdb'
      blastRootDirectory = '/tmp/BLAST'
    os.system(os.path.join(blastRootDirectory, formatdb) + ' -i ' + os.path.join(blastRootDirectory, 'blastDB.fasta -o T'))
    print 'done'
    
  return dictionary_db

def get_seqs(blastRootDirectory):
  
  if len(sys.argv) >= 2:
      numSeqs = int(sys.argv[1])
      if numSeqs < 0 or numSeqs > 100000:
        print 'requested number of sequences is outside allowable range (1-100000). Using default (1000)'
        numSeqs = 10
  else: numSeqs = 10
  print 'requesting', numSeqs, 'query sequences from the server'  
  seqs = phamServer.request_seqs(server, numSeqs, client)
      
  '''Builds the file to be blasted from the sequences given'''
      
  f = open(os.path.join(blastRootDirectory, 'filetoblast.txt'), 'w')
    
    
  print seqs
    
  '''takes the new set of sequences and checks if they exist in the local database
  and, if so, writes the sequence id and translation to a separate FASTA formated input
  file to be passed to the BLASTALL executable'''
  
  for GeneID in seqs:      
      parser = Fasta.RecordParser()

      infile = open(os.path.join(blastRootDirectory,'blastDB.fasta'))
      
      iterator = Fasta.Iterator(infile, parser)
      while 1:
        record = iterator.next()
        if not record:
          break
        record_id = record.title
          
        if GeneID == record_id:
          f.write('>' + record.title + '\n' + record.sequence + '\n')
    
  f.close()  
  return (len(seqs))  
  #if len(seqs) == 0:
  #  print 'server returned no sequences to align.\nExiting...'
  #  sys.exit()

def main():
  if sys.platform == 'win32':
    # this will just use the current working directory
    blastRootDirectory = ''
  else:
    blastRootDirectory = os.path.join(os.getcwd(), '../../BLAST/')
  
  '''initializes db'''
  dictionary_db = {'data': ""}
  #dictionary_db = check_db(dictionary_db=None, blastRootDirectory=blastRootDirectory)
   
  '''Retrieves sequences to BLAST, BLASTs, and reports scores infinitely'''
  while 1:
    dictionary_db = check_db(dictionary_db, blastRootDirectory)
    print 'getting sequences to align'
    if get_seqs(blastRootDirectory) == 0:
      time.sleep(5)
    else: 
      nonmatchingQueries, results = blast(blastRootDirectory)
      if nonmatchingQueries:
        phamServer.report_non_matching_queries(nonmatchingQueries, server, client)
      phamServer.report_scores(results, server, client)
    #print 'sleeping for 15 seconds'
    #time.sleep(15)

if __name__ == '__main__':
  
  main()
  
