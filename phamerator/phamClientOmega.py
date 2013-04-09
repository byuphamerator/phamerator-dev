#!/usr/bin/env python

import os, sys, time, socket, getopt, getpass
import Pyro.core
from Pyro.EventService.Clients import Subscriber
from Bio.Align.Applications import ClustalwCommandline
import Bio
if float(Bio.__version__) < 1.56:
  from Bio.Clustalw import MultipleAlignCL
  from Bio import Clustalw
import logger
import pp
from db_conf import db_conf

class options:
  def __init__(self, argv):
    try:
      opts, args = getopt.getopt(argv, "hpu:n:", ["help", "password", "user=", "nsname="])
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
      elif opt in ("-u", "--user"):
        self.argDict['user'] = arg
      elif opt in ("-n", "--nsname"):
      	self.argDict['nsname'] = arg
    if not self.argDict.has_key('password'): self.argDict['password'] = ''
    required_args = ('user', 'nsname')
    for a in required_args:
      if a not in self.argDict:
        print "required argument '%s' is missing" % a
        self.usage()
        sys.exit()

  def usage(self):
    '''Prints program usage information'''
    print """phamClient.py [OPTION] [ARGUMENT]
             -h, --help: print this usage information
             -u, --user=<username>: specify a username on the database
             -p, --password: prompt for a password
             -n, --nsname=<nsname>: nsname of PYRO server, required
"""

class clustalwAligner(Subscriber):
  def __init__(self, username, password):
    self.username = username
    self.password = password
    #Pyro.config.PYRO_NS_HOSTNAME='136.142.141.113' #djs
    if opts['nsname']:
      Pyro.config.PYRO_NS_HOSTNAME=opts['nsname']
    else:
      Pyro.config.PYRO_NS_HOSTNAME='localhost'
    Subscriber.__init__(self)
    self.subscribe("clustalw")
    self._logger = logger.logger(sys.argv[2])
    #Pyro.config.PYRO_NS_HOSTNAME='djs-bio.bio.pitt.edu'
    self.serverSelector = Pyro.core.getProxyForURI("PYRONAME://serverSelector")
    print 'selector:', self.serverSelector
    self._logger.log('got serverSelector')
    self.client = socket.gethostname()
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

    self.align()

  def event(self, event):
    self._logger.log('%s --> %s' % (event.subject, event.msg))
    if event.subject == 'clustalw' and event.msg == 'update available':
      self.align()
  
  def run_clustalw(clustalw_infile, qid, sid):
    """works with biopython version 1.56 or newer"""
    from Bio.Align.Applications import ClustalOmegaCommandline
    from Bio import AlignIO
    cline = ClustalOmegaCommandline("clustalw", infile = clustalw_infile)
    stdout, stderr = cline()
    alignment = AlignIO.read(clustalw_infile.replace('.fasta', '.aln'), "clustal")
    return (qid, sid, alignment)
 
  def run_clustalw_old(qid, sid, cline):
    """works with biopython versions older than 1.56"""
    alignment = Bio.Clustalw.do_alignment(cline)
    return (qid, sid, alignment)

  def cleanup_temp_files(self, open_files):
    for file in open_files:
      #print 'purging temp file %s' % file
      os.remove(file)

  def process_jobs(self, jobs, results, open_files):
    for job in jobs:
      query_id, subject_id, alignment = job()
      #print 'query_id: %s\nsubject_id: %s\nalignment: %s' % (query_id, subject_id, alignment)
      length = alignment.get_alignment_length()
      star = alignment._star_info.count('*')
      score = float(star)/length
      #print query_id, subject_id#, alignment
      #print 'length:', length, 'identical:', star, 'score:', score
      #_logger.log queryName, subjectName, score
      if score >= 0.275:
        results.append((query_id, subject_id, score))
      #self._logger.log('reporting scores back to server')
    self.cleanup_temp_files(open_files)
    return results

  def align(self):
    id = True
    ppservers = ()
    job_server = pp.Server(ppservers=ppservers,secret="secret")
    while id: # this should test to make sure there are still alignments to do
      print 'getting work unit'
      try:
        clustalw_work_unit = self.phamServer.request_seqs(self.client)
        if not clustalw_work_unit.query_id:
          print 'no work units available...sleeping'
          logo = os.path.join(os.path.dirname(__file__),"pixmaps/phamerator.png")
          #print "logo: %s" % logo
          try:
            import pynotify
            if pynotify.init("Phamerator"):
              n = pynotify.Notification("Phamerator Update", "No Clustalw alignments left to do...sleeping", "file:///%s" % logo)
              n.show()
            else:
              pass
              #print "there was a problem initializing the pynotify module"
          except:
            pass
          time.sleep(30)


          continue
      except Exception, x:
        print ''.join(Pyro.util.getPyroTraceback(x))
      server, db = self.phamServer.request_db_info()
      #c = db_conf(username=self.username, password=self.password, server=server, db=db)
      #clustalw_work_unit.set_cursor(c)
      print 'got it'

      try:
        import pynotify
        if pynotify.init("Phamerator"):
          logo = os.path.join(os.path.dirname(__file__),"pixmaps/phamerator.png")
          #print "logo: %s" % logo
          n = pynotify.Notification("Phamerator Update", "Clustalw alignments in progress for id %s" % clustalw_work_unit.query_id, "file:///%s" % logo)
          n.show()
        else:
          pass
          #print "there was a problem initializing the pynotify module"
      except:
        pass

      self._logger.log('aligning sequences')
###########################################################################
#			                BEGIN MATT'S ALTERATIONS          #
#                                                                         #
###########################################################################
      results = []
      open_files = []
      # tuple of all parallel python servers to connect with

      # Creates jobserver with automatically detected number of workers

      #grab number of processors
      numcpus = job_server.get_ncpus()
      print "numcpus =",numcpus
      
      #for n, person in enumerate(people):
      #for seq in seqs:
      jobs = []
      #for i,currentseq in enumerate(seqs):
      query_id = clustalw_work_unit.query_id
      query_translation = clustalw_work_unit.query_translation
      counter = 0
      for record in clustalw_work_unit.database:
        subject_id, subject_translation = record.id, record.translation
        fname = os.path.join(self.rootdir, 'temp' + query_id + '_' + subject_id + '.fasta')
        f = open(fname, 'w')
        open_files.append(fname)
        open_files.append(fname.replace('.fasta','.dnd'))
        open_files.append(fname.replace('.fasta','.aln'))
        f.write('>%s\n%s\n>%s\n%s\n' % (query_id, query_translation, subject_id, subject_translation))
        f.close()

        clustalw_infile = os.path.join(self.rootdir, 'temp' + str(query_id) + '_' + str(subject_id) + '.fasta')

        if float(Bio.__version__) >= 1.56:
          # pass the query id (qid) and the subject id (sid) to run_clustalw
          jobs.append(job_server.submit(clustalwAligner.run_clustalw, (clustalw_infile, query_id, subject_id), (), ()))
        else:
          cline = MultipleAlignCL(clustalw_infile)
          cline.set_output(os.path.join(self.rootdir, 'temp' + str(query_id) + '_' + str(subject_id) + '.aln'))
          # pass the query id (qid) and the subject id (sid) to run_clustalw
          jobs.append(job_server.submit(clustalwAligner.run_clustalw_old, (query_id, subject_id,cline), (), ("Bio.Clustalw",)))

        counter = counter + 3
        if counter > 50:
          results = self.process_jobs(jobs, results, open_files)
          jobs = []
          open_files = []
          counter = 0

      results = self.process_jobs(jobs, results, open_files)
      jobs = []
      open_files = []
      counter = 0
      # must report everything back in atomic transaction
      print 'reporting scores back to server'
      try:
        self.phamServer.report_scores(clustalw_work_unit, results, self.client)
      except Exception, x:
        print ''.join(Pyro.util.getPyroTraceback(x))
        print 'exiting on pyro traceback'
        sys.exit()

opts = options(sys.argv[1:]).argDict
username, password = opts['user'], opts['password']


aligner = clustalwAligner(username, password)
aligner.listen()
