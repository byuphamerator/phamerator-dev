from errorHandler import *
from phamerator_manage_db import *
from db_conf import db_conf

class workUnitSeq:
  def __init__(self, id, translation):
    self.id = id
    self.translation = translation

class alignmentWorkUnit(errorHandler):
  def __init__(self, c):
    errorHandler.__init__(self)
    #self.c = c
    self.alignments = {}

#class clustalwWorkUnit(alignmentWorkUnit, errorHandler):
class clustalwWorkUnit(errorHandler):
  def __init__(self, c, query_id=None):
    errorHandler.__init__(self)
    if not query_id:
      sqlQuery = "SELECT id FROM gene WHERE clustalw_status = 'avail' LIMIT 1"
      try:
        c.execute(sqlQuery)
        try:
          self.query_id = str(int(c.fetchall()[0][0]))
        except:
          self.query_id = None
          return
      except: self.show_sql_errors(c)
    self._mark_pending(c)
    self.query_translation = get_translation_from_id(c, self.query_id)
    self.create_database(c)

  def set_cursor(self, c):
    pass
    #self.c = c

  def _mark_pending(self, c):
    sqlQuery = "update gene set clustalw_status = 'pending' where id = %s" % self.query_id
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def create_database(self,c):
    self.database = []
    sqlQuery = "select id, translation from gene where id < %s" % self.query_id 
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    for result in c.fetchall():
      record = workUnitSeq(str(int(result[0])), result[1])
      self.database.append(record)

  def add_matches(self, matches, c):
    '''called by a compute node to keep track of a good clustalw alignment'''
    # matches = [(qid1, sid1, score1), (qid2, sid2, score2), ...]
    for qid, sid, score in matches:
      self._add_match(qid, sid, score, c)
    sqlQuery = "UPDATE gene SET clustalw_status = 'done' WHERE id = %s" % self.query_id
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def _add_match(self, qid, sid, score, c):
    '''add a good alignment score to the database'''
    # qid and sid are gene table id's for the query and subject
    q = get_GeneID_from_id(c, qid)
    s = get_GeneID_from_id(c, sid)
    sqlQuery = """INSERT INTO scores_summary(query, subject, clustalw_score) VALUES('%s', '%s', ROUND(%s,4))""" % (q, s, score)
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def get_matches(self, qid):
    '''called by server when adding good clustalw alignment(s) to MySQL db'''
    if self.alignments.has_key(qid):
      return self.alignments[qid]
    return None

class blastWorkUnit(errorHandler):
  def __init__(self, c, query_id=None):
    errorHandler.__init__(self)
    sqlQuery = "SELECT id FROM gene WHERE blast_status = 'avail' LIMIT 1"
    try:
      c.execute(sqlQuery)
      try:
        self.query_id = str(int(c.fetchall()[0][0]))
      except:
        self.query_id = None
        return
    except: self.show_sql_errors(c)

    self._mark_pending(c)
    self.query_translation = get_translation_from_id(c, self.query_id)
    self.create_database(c)

  def _mark_pending(self, c):
    sqlQuery = "update gene set blast_status = 'pending' where id = %s" % self.query_id
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def create_database(self, c):
    self.database = []
    sqlQuery = "select id, translation from gene"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    print 'rowcount: %s' % c.rowcount
    for result in c.fetchall():
      record = workUnitSeq(result[0], result[1])
      self.database.append(record)

  def get_as_fasta(self):
    fasta = ""
    for record in self.database:
      fasta = "%s>%s\n%s\n" % (fasta, record.id, record.translation)
    return fasta

  def add_matches(self, matches, c):
    '''called by a compute node to keep track of a good BLASTp alignment'''
    # matches = [(qid1, sid1, score1), (qid2, sid2, score2), ...]
    for qid, sid, e, bits in matches:
      self._add_match(qid, sid, e, bits, c)
    sqlQuery = "UPDATE gene SET blast_status = 'done' WHERE id = %s" % self.query_id
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def _add_match(self, qid, sid, e, bits, c):
    '''called by a compute node to keep track of a good BLAST alignment'''
    # qid and sid are gene table id's for the query and subject
    q = get_GeneID_from_id(c, qid)
    s = get_GeneID_from_id(c, sid)
    sqlQuery = """INSERT INTO scores_summary(query, subject, blast_score, blast_bit_score)
                VALUES('%s', '%s', '%s', '%s')""" % (q, s, e, bits)
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)
    sqlQuery = "COMMIT"
    try: c.execute(sqlQuery)
    except: self.show_sql_errors(c)

  def get_matches(self, qid):
    '''called by server when adding good BLAST alignment(s) to MySQL db'''
    if self.alignments.has_key(qid):
      return self.alignments[qid]
    return None
