#!/usr/bin/env python2.5

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Copyright Steve Cresawn, 2006-2009

import db_conf

import sys, getopt, getpass, Bio
from Bio import GenBank

class BlastDatabase:
  def __init__(self):
    self.blast_db = "./Databases/nr/nr"
    self.blast_file = "./Databases/test/query.fasta"
    self.blast_exe = "/home/steve/Applications/BLAST/bin/blastall"
  def update_database(self):
    '''check to see if the specified database is available, and if so, whether
    it is up to date'''
    # run update_blastdb.pl

  def do_blast_search(self):
    from Bio.Blast import NCBIStandalone
    self.result_handle, self.error_handle = NCBIStandalone.blastall(self.blast_exe, "blastp",
                                                      self.blast_db, self.blast_file)

  def parse_results(self):
    from Bio.Blast import NCBIXML
    self.blast_records = NCBIXML.parse(self.result_handle)

class BlastResults:
  '''contains records from a blast search and methods to process them'''
  def __init__(self, blast_records):
    self.blast_records = blast_records
  def process_records(self):
    while 1:
      try:
        blast_record = self.blast_records.next()
      except StopIteration:
        break
      E_VALUE_THRESH = 1e-4
      print 'query: %s' % blast_record.query
      for alignment in blast_record.alignments:
        for hsp in alignment.hsps:
            if hsp.expect < E_VALUE_THRESH:
                #print '****Alignment****'
                print 'sequence:', alignment.title
                print 'length:', alignment.length
                print 'e value:', hsp.expect
                #print hsp.query[0:75] + '...'
                #print hsp.match[0:75] + '...'
                #print hsp.sbjct[0:75] + '...'

def usage():
  '''Prints program usage information'''
  print """blast_genbank.py [OPTION] [ARGUMENT]
           -h, --help: print this usage information
           -u, --username: database username
           -p, --password: prompt for a database password
           -s, --server: address of the database server
           -d, --database: name of the database on the server"""

def parse_opts(argv):
  try:                                
    opts, args = getopt.getopt(argv, "hpu:s:d:", ["help", "password", "username=", "server=", "database="])
    username = password = server = database = ""
  except getopt.GetoptError:
    print 'Error parsing options'
    usage()
    sys.exit(2)
  if 'server' not in opts: server = 'localhost'
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
  optDict = {}
  if None in [username, password, server, database]:
    usage()
    sys.exit()
  optDict['username'], optDict['password'], optDict['server'], optDict['database'] = \
          username, password, server, database
  return optDict

def create_cursor(optDict):
  c = db_conf.db_conf(username=optDict['username'], password=optDict['password'],
      server=optDict['server'], db=optDict['database']).get_cursor()
  return c

def main(argv):
  optDict = parse_opts(argv)
  c = create_cursor(optDict)
  bdb = BlastDatabase()
  bdb.do_blast_search()
  bdb.parse_results()
  br = BlastResults(bdb.blast_records)
  br.process_records()
  
if __name__ == '__main__':
  main(sys.argv[1:])
