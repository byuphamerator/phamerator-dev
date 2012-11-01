from Bio import GenBank
try:
  from Bio import Entrez
except:
  pass
import time

class query:
  def __init__(self, query_string, allowRefSeqs=False):
    self.query_string = query_string
    self.allowRefSeqs = allowRefSeqs
    #self.result = ''

  def search(self, query):
    handle = Entrez.esearch(db="nucleotide",term=query)
    gi_list = Entrez.read(handle)['IdList']
    return gi_list

  def run(self):
    if not self.allowRefSeqs:
      print 'NOT ALLOWING REFSEQS'
      if self.query_string.startswith('GI:') or self.query_string.startswith('gi:'):
        self.query_string = self.query_string[3:]
        q = self.query_string
        gi_list = self.search(q)
      else:
        q = "mycobacterium phage " + self.query_string + " AND Hatfull GF[AUTH] NOT srcdb_refseq[prop]"
        print "search query:", q
        gi_list = self.search(q)
        print 'gi_list:', gi_list
      if len(gi_list) == 0:
        print 'Got no results.  Changing search criteria'
        q = self.query_string + " AND Hatfull GF[AUTH] NOT srcdb_refseq[prop]"
        print "search query:", q
        gi_list = self.search(q)
      if len(gi_list) == 0:
        print 'Got no results.  Changing search criteria'
        q = self.query_string + " NOT srcdb_refseq[prop]"
        print "search query:", q
        gi_list = self.search(q)
      if len(gi_list) != 0:
        print 'found GenBank Direct Submission(s)'
        print gi_list
      else:
        print 'found no results other than refSeq(s), which you refused'
        self.result = None
        return
    else: # allowing refSeqs
      print 'ALLOWING REFSEQS'
      if self.query_string.startswith('GI:') or self.query_string.startswith('gi:'):
        self.query_string = self.query_string[3:]
        q = self.query_string
        gi_list = self.search(q)
      else:
        q = "mycobacterium phage " + self.query_string + " AND Hatfull GF[AUTH]"
        print "search query:", q
        gi_list = self.search(q)
      if len(gi_list) == 0:
        q = self.query_string + " AND Hatfull GF[AUTH]"
        gi_list = self.search(q)
      if len(gi_list) == 0:
        print 'Got no results.  Changing search criteria'
        print 'search query:', self.query_string
        gi_list = self.search(self.query_string)

      if len(gi_list) == 0:
        print 'no results found'

    self.results = gi_list
    return

    if len(gi_list) > 1:
      selection = -1
      for i in range(len(gi_list)):
        print i+1, '\t', gi_list[i]
      selection = raw_input("Your search returned multiple results.  Please type the number for your selection: ")
      selection = int(selection) - 1
    else:
      selection = 0
    print 'creating parser...'
    feature_parser = GenBank.FeatureParser()
    print 'creating dict'
    ncbi_dict = GenBank.NCBIDictionary('nucleotide', 'genbank', parser = feature_parser)

    if selection == -1: ## Accounts for non-existent phage query
      print 'non-existent phage query'
      self.result = 0
    else:
      print 'got result'
      self.result = ncbi_dict[gi_list[selection]]
