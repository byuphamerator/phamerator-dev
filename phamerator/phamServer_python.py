#!/usr/bin/env python

import db_conf
import Pyro.core
import Pyro.naming
import getopt
from threading import Thread
from Pyro.EventService.Clients import Subscriber
from Pyro.protocol import getHostname
import Pyro.EventService.Clients
Pyro.config.PYRO_NS_HOSTNAME='djs-bio.bio.pitt.edu'
#Pyro.config.PYRO_NS_HOSTNAME=getHostname()

class node(Pyro.EventService.Clients.Publisher, Subscriber):
  '''the main class for a compute node'''
  def __init__(self):
    Pyro.EventService.Clients.Publisher.__init__(self)
    Subscriber.__init__(self)
    self.hostname=getHostname()
    self.subscribe('question')
    self.subscribe('misc')
    self.doneAlignments = alignments(status='avail', source='disc')
    self.availAlignments = alignments(status='avail', source='db')
    self.seqs = seqs()
    self.publishInfo('misc', '%s is running' % self.hostname)
  def event(self, event):
    # received a generic event -> figure out which local method to call to handle it
    # first, is it a question or an answer?

    # this is an answer, and since I'm subscribed to 'answer' I probably asked the question
    if event.subject == 'answer':
      answer = event.msg
      num == answer['answer']
      who == answer['who'] # who sent this answer?
      if answer['question'] == 'number of availAlignments':
        if num > 0: who.send_availAlignments()

    # this is a question that some other node asked, so I should answer
    if event.subject == 'question':
      question = event.msg
      if question['question'] == 'number of availAlignments': self.send_num_of_availAlignments()

  def send_num_of_availAlignments(self):
    '''called when another node is looking for availAlignments and wants to know if this node has any'''
    answer = {'question': 'number of availAlignments','who': self.hostname, 'answer': len(self.availAlignments)}
    self.publishInfo('answer', answer)
  def send_availAlignments(self, toNode):
    '''called when another node wants some of my alignments to do'''
    # send some availAlignments to node_id when node_id confirms receipt, delete from local copy of availAlignments
    num = len(self.availAlignments)/2
    toNode.receive_availAlignments(self.availAlignments[:num])
    self.availAlignments = self.availAlignments[num:] 
    #return self.availAlignments
  def send_doneAlignments(self):
    '''called when another node wants to compare scores on done alignments'''
    # TODO: PYRO: ask over Pyro for doneAlignments from the other nodes
    self.publishInfo('doneAlignments', self.doneAlignments)
  def do_alignments(self):
    '''whenever idle, do alignments and move them from self.availAlignments to self.doneAlignments'''
    # if there are no availAlignments, find out if any other node has some
    if self.availAlignments:
      question = {'asker':self.hostname, 'question':'number of availAlignments'}
      self.subscribe('answer')
      self.publishInfo('question', question)
      # call someOtherNode.send_availAlignments()
  def save_alignments(self):
    pass
    # periodically, pickle and write both self.doneAlignments and self.availAlignments
  def publishInfo(self, channel, message):
    #publish various Pyro events
    self.publish(channel, message)

class seqs:
  '''dict holding each GeneID and sequence'''
  def __init__(self,username=None,password=None,server=None,database=None):
    if username and password and server and database:
      self.c = db_conf.db_conf(username=username,password=password,server=server,db=database).get_cursor()
      self.c.select(gene,GeneID, translation)
      self.seqs = {} # key is fasta header, value is sequence
      genes = c.fetchall()
      for g, t in genes:
        self.seqs[g] = t
    else:
      # TODO: PYRO: request sequences from other nodes using pyro
      pass
  def get_seqs(self):
    while self.busy:
      time.sleep(1)
    return self.seqs

class align:
  '''holds query and subject GeneIDs, score, type, and times computed for a single alignment'''
  def __init__(self, header, type, score=None):
    h1, h2 = header[0], header[1]
    s1,s2=len(seqs[h1]), len(seqs[h2])
    if s2>s1: self.header = [h1,h2] # put shortest sequence first
    elif s1>s2: self.header = [h2,h1]
    else:
      if h1<h2: self.header = [h1,h2]
      else: self.header = [h2,h1]
    self.type = type
  def __cmp__(self, other):
    if self.headers == other.headers: return 0
    elif self.headers > other.headers: return 1
    else: return -1

class alignments:
  '''a container for many individual alignments'''
  def __init__(self, status=None, source='db'):
    if not status:
      print 'you must first set the requested status'
      sys.exit()
    self.aligns = self.create_aligns() # list of aligns
  def create_aligns(self):
    alignHeaders = []
    for q in seqs.keys(): # seqs is an instance of the 'seq' class
      for s in seqs.keys():
        if q == s: continue # don't align a sequence to itself
        if len(seqs[q]) > len(seqs[s]): alignHeaders.append([s,q])
        elif len(seqs[s]) > len(seqs[q]): alignHeaders.append([q,s])
        else: # if sequences are the same length, sort alphabetically
          headers = [q,s]
          headers.sort()
          alignHeaders.append(headers)
    for h in alignHeaders:
      #
      self.add(h[0],h[1],None)
      self.aligns.append(align(a[0], a[1], None, None))
  def add_alignment(alignment):
    if alignment not in self.aligns:
      self.aligns.append(alignment)
    else:
      i=self.aligns.index(alignment)
      if self.aligns[i].score == alignment.score:
        self.aligns[i].times_computed+=1
      else: raise scoreError
  def remove_alignment(alignment):
    self.aligns.remove(alignment)

  #def assign(): # called when another client requests work
  #  donated = self.aligns[:1000]
  #  self.aligns = self.aligns[1000:]
  #  return donated

def main():
  server = 'djs-bio.bio.pitt.edu'
  daemon=Pyro.core.Daemon(host=getHostname())
  app = node()
  daemon.connect(app,getHostname())

  #if os.path.exists('somefile'):
  #  availAligns = unpickle('somefile')
  #else:
  #  availAligns = alignments()
  #if os.path.exists('someotherfile'):
  #  doneAligns = unpickle('someotherfile')
  #else:
  #  doneAligns = alignments()

if __name__ == '__main__':
  main()
