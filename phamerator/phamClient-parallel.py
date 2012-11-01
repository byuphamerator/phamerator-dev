#!/usr/bin/env python

import os, sys, time, socket
import Pyro.core
from Pyro.EventService.Clients import Subscriber
from Bio.Clustalw import MultipleAlignCL
from Bio import Clustalw
import logger
import pp

class clustalwAligner(Subscriber):
  def __init__(self):
    Pyro.config.PYRO_NS_HOSTNAME='134.126.132.72' #djs
    #Pyro.config.PYRO_NS_HOSTNAME='hatfull12.bio.pitt.edu'
    Subscriber.__init__(self)
    self.subscribe("clustalw")
    self._logger = logger.logger(sys.argv[2])
    #Pyro.config.PYRO_NS_HOSTNAME='djs-bio.bio.pitt.edu'
    self.serverSelector = Pyro.core.getProxyForURI("PYRONAME://serverSelector")
    print 'selector:', self.serverSelector
    self._logger.log('got serverSelector')
    self.client = socket.gethostname()
    if self.client in ('phage', 'gene', 'pham'):
      self.client = self.client + '_hostname'
    self._logger.log('platform: ' + sys.platform)
    self._logger.log('hostname: ' + self.client)
    self.server = self.serverSelector.get_server(sys.platform, self.client)
    self._logger.log('using server ' + self.server)
    self.phamServer = Pyro.core.getProxyForURI("PYRONAME://"+self.server)
    if sys.platform == 'win32':
      # this will just use the current working directory
      self.rootdir = ''
    else:
      self.rootdir = '/tmp'

    if len(sys.argv) < 2:
      self._logger.log('Number of sequences to align not specified.  Using default (1000)')
      self.numSeqs = 1000
    elif int(sys.argv[1]) < 0 or int(sys.argv[1]) > 10000:
      self._logger.log('requested number of sequences (%s) is outside allowable range (1-10000). Using default (1000)' % sys.argv[1])
      self.numSeqs = 1000
    else:
      self.numSeqs = int(sys.argv[1])
    self.align()

  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
    if event.subject == 'clustalw' and event.msg == 'update available':
      self.align()

  def run_clustalw(id,cline):
    alignment = Bio.Clustalw.do_alignment(cline)
    return (id,alignment)

  def align(self):
    seqs = True
    while seqs:
      seqs = self.phamServer.request_seqs(self.server, self.numSeqs, self.client)
      try:
        import pynotify
        if pynotify.init("Phamerator"):
          n = pynotify.Notification("Phamerator Update", "doing clustalw alignments", "file:///home/steve/Applications/git/PhamDB/phageManager_logo.png")
          n.show()
        else:
          pass
          #print "there was a problem initializing the pynotify module"
      except:
        pass
      if len(seqs) == 0:
        self._logger.log('server returned no sequences to align.')
        return
      self._logger.log('server returned ' + str(len(seqs)) + ' to align')
      self._logger.log('aligning sequences')
      results = []
###########################################################################
#			                BEGIN MATT'S ALTERATIONS			                      #
#									                                                        #
###########################################################################
      # tuple of all parallel python servers to connect with
      ppservers = ()

      # Creates jobserver with automatically detected number of workers
      job_server = pp.Server(ppservers=ppservers)

      #grab number of processors
      numcpus = job_server.get_ncpus()
      print "numcpus =",numcpus
      
      #for n, person in enumerate(people):
      #for seq in seqs:
      for i,currentseq in enumerate(seqs):
        jobs = []
        id, querySeq, subjectSeq = currentseq
        f = open(os.path.join(self.rootdir, 'temp' + str(i) + '.fasta'), 'w')
        f.write('>' + 'a' + '\n' + querySeq + '\n>' + 'b' + '\n' + subjectSeq + '\n')
        f.close()
        cline = MultipleAlignCL(os.path.join(self.rootdir, 'temp' + str(i) + '.fasta'))
        #cline.is_quick = True
        cline.set_output(os.path.join(self.rootdir, 'temp' + str(i) + '.aln'))
        #alignment = Clustalw.do_alignment(cline)
        #jobs = [(input, job_server.submit(sum_primes,(input,), (isprime,), ("math",))) for input in inputs]
        jobs.append(job_server.submit(clustalwAligner.run_clustalw, (id,cline), (), ("clustalwAligner.run_clustalw","Bio.Clustalw",)))
      
      for job in jobs:
        id,alignment = job()
        length = alignment.get_alignment_length()
        star = alignment._star_info.count('*')
        score = float(star)/length
        #print 'length:', length, 'identical:', star, 'score:', score
        #_logger.log queryName, subjectName, score
        results.append((id, score))
      self._logger.log('reporting scores back to server')
      self.phamServer.report_scores(results, self.server, self.client)
      #return results

aligner = clustalwAligner()
aligner.listen()

#while 1:
  #_logger.log('getting sequences to align')
  #try:
  #seqs = aligner.phamServer.request_seqs(server, numSeqs, client)
  #if len(seqs) == 0:
  #  aligner._logger.log('server returned no sequences to align.')
  #  sys.exit()
  #else: aligner._logger.log('server returned ' + str(len(seqs)) + ' to align')
  #aligner._logger.log("got sequences")
  #results = aligner.align(seqs)
  #aligner.phamServer.report_scores(results, server, client)
  #phamServer.ping(client)
  #time.sleep(1)
  #except:
  #  sleep_delay = int(sleep_delay*1.5)
  #  _logger.log('sleeping for ' + str(sleep_delay) +  ' seconds')
  #  time.sleep(sleep_delay)
