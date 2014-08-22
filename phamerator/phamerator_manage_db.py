#!/usr/bin/env python

import pdb
import Bio
from Bio import GenBank
from Bio import SeqIO
from Bio import AlignIO
from Bio.Align.Applications import ClustalwCommandline
from Bio.Seq import Seq, translate
import getopt, getpass, signal, sys, os, MySQLdb, re, query, db_conf, time, string, pickle
import Pyro.EventService.Clients
import ConfigParser

class phamPublisher(Pyro.EventService.Clients.Publisher):
  '''Publishes Pyro events over the network to clients, for instance when the BLAST database changes'''
  Pyro.config.PYRO_NS_HOSTNAME='ip94-195.pc.jmu.edu'
  def __init__(self):
    Pyro.EventService.Clients.Publisher.__init__(self)
  def publish_db_update(self, channel, message):
    self.publish(channel, message)

def get_pham_history(c, child=None, parent=None):
  '''get all the children of the specified parent or the parent of the specified child'''
  if not child and not parent:
    print 'Error.  Must specify child or parent'
    return None
  if child and parent:
    print 'Error.  Must specify child or parent, not both'
    return None
  if child and not parent:
    sqlQuery = "SELECT parent from pham_history WHERE name = '%s'" % child
    c.execute(sqlQuery)
    i = c.fetchall()
    if len(i) > 1:
      print '#' * 80
      print 'Error.  Pham %s has more than one parent pham'
      print '#' * 80
      return None
    if len(i) == 0:
      return None
    return int(i[0][0])
  if parent and not child:
    sqlQuery = "SELECT name from pham_history WHERE parent = '%s'" % parent
    c.execute(sqlQuery)
    i = c.fetchall()
    if len(i) == 0:
      return None
    children = []
    for row in i:
      children.append(int(row[0]))
    return children

def remove_phage_from_db(PhageID, c, confirm=True):
  try:
    from phamerator import plugins
    from phamerator.plugins import phamchecker
  except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from phamerator import plugins
    from phamerator.plugins import phamchecker

  c.execute("SELECT COUNT(*) FROM phage WHERE PhageID = '%s'" % PhageID)
  print "SELECT COUNT(*) FROM phage WHERE PhageID = '%s'" % PhageID
  count = c.fetchone()[0]
  print count
  if not count:
    sqlQuery = "SELECT name, PhageID FROM phage WHERE name LIKE '%%%s%%'" % PhageID
    c.execute(sqlQuery)
    nP = c.fetchall()
    if len(nP) == 0:
      print '%s was not found in the database.  Giving up.' % PhageID
      return
    elif len(nP) > 1:
      print "More than one phage was found with a name like '%s' (see below).  Please try again using the PhageID or a more specific name." % PhageID
      print "PhageID\tName"
      for name, PhageID in nP: print PhageID + '\t' + name
      return
    else:
      name, PhageID = nP[0]
      print "Found phage '%s' with PhageID '%s'." % (name, PhageID)
  c.execute("SELECT COUNT(*) FROM pham")
  numPhams = c.fetchone()[0]
  if numPhams == 0: print 'No pham assignments have been made.  Deleting phage without confirmation.'
  else:
    if confirm:
      print 'Deleting a genome usually invalidates the current pham assignments.'
      go = raw_input("Delete pham assignments [Y/n]:").upper()
      if go == 'Y':
        c.execute("TRUNCATE TABLE pham")
        print 'pham table reset'
      else:
        go = raw_input("Are you sure you know what you're doing? [y/N]:").upper()
        if go != 'Y':
          print 'Aborting on user request.  No changes to the database were made.'
          return

    # delete appropriate rows from pham, pham_color, and pham_old, and figure out what to do with pham_history
    phams = get_phams_from_PhageID(c, PhageID)
    #print 'phams: %s' % phams
    genes = get_genes_from_PhageID(c, PhageID)
    #print 'genes: %s' % genes
    # delete all blast scores from the scores_summary table

    # Don't delete these rows, just recalculate the e-values from the bit scores!
    #sqlQuery = "DELETE FROM scores_summary WHERE blast_score IS NOT NULL"
    #try:
    #  c.execute(sqlQuery)
    #  print '%s rows deleted from scores_summary' % c.rowcount
    #except:
    #  print "'error deleting from scores summary: %s'" % sqlQuery
    #  c.execute("SHOW WARNINGS")
    #  errors = c.fetchall()
    #  for error in errors:
    #    print error

    for GeneID in genes:
      print "GeneID: %s" % GeneID
      # delete any rows from scores_summary where this gene is the subject or query
      sqlQuery = "DELETE FROM scores_summary WHERE query = '%s' OR subject = '%s'" % (GeneID, GeneID)
      try:
        c.execute(sqlQuery)
        print '%s rows deleted from scores_summary' % c.rowcount
      except:
        print "'error deleting from scores summary: %s'" % sqlQuery
        c.execute("SHOW WARNINGS")
        errors = c.fetchall()
        for error in errors:
          print error

      phamName = get_pham_from_GeneID(c, GeneID)
      #print 'GeneID: %s, phamName: %s' % (GeneID, phamName)
      #parent = get_pham_history(c, child=phamName):
      if phamName:
        children = []
        child_list = get_pham_history(c, parent=phamName)
        if child_list:
          for child in child_list:
            children.append(child)

      else: continue
      print 'phamName: %s :: children: %s' % (phamName, children)
      if not children:
        # delete all the genes added to this pham after this gene, unless that would
        # delete all the genes in the pham. In the latter case, this would cause genes
        # to forget their phamName, since there would no reason to add them back later
        # with the current phamName

        sqlQuery = "SELECT orderAdded from pham WHERE pham.GeneID = '%s'" % GeneID
        try: c.execute(sqlQuery)
        except:
          print "'error: %s'" % sqlQuery
          c.execute("SHOW WARNINGS")
          errors = c.fetchall()
          for error in errors:
            print error

        o = c.fetchone()[0]

        sqlQuery = "SELECT count(*) FROM pham WHERE name = '%s' AND orderAdded < %s" % (phamName, o)
        try: c.execute(sqlQuery)
        except:
          print "error: %s" % sqlQuery
          c.execute("SHOW WARNINGS")
          errors = c.fetchall()
          for error in errors:
            print error

        geneCount = int(c.fetchone()[0])
        print 'geneCount: %s' % geneCount

        if geneCount:
          sqlQuery = "SELECT MIN(orderAdded) FROM pham WHERE name = '%s'" % phamName
          c.execute(sqlQuery)
          min = c.fetchone()[0]
          #print 'deleting from %s where orderAdded > %s' % (phamName, min)
          sqlQuery = "DELETE pham from pham, gene, phage WHERE pham.GeneID = gene.GeneID and gene.PhageID = phage.PhageID AND pham.name = '%s' AND orderAdded > '%s'" % (phamName, min)
          try: c.execute(sqlQuery)
          except:
            print "'error: %s'" % sqlQuery
            c.execute("SHOW WARNINGS")
            errors = c.fetchall()
            for error in errors:
              print error
          print 'deleted', c.rowcount, 'rows from pham'

        else:
          # this gene is the founder of this phamily, so delete this gene only (and the next gene will be the new founder)
          sqlQuery = "DELETE pham from pham, gene, phage WHERE pham.GeneID = '%s'" % (GeneID)
          try: c.execute(sqlQuery)
          except:
            print "'error: %s'" % sqlQuery
            c.execute("SHOW WARNINGS")
            errors = c.fetchall()
            for error in errors:
              print error
          print 'deleted', c.rowcount, 'rows from pham'

      if children:
        c.execute('commit')
        # if this pham has children, see if deleting this gene will screw up the integrity of the pham
        # if it does, then add children back to pham table and delete other genes from pham
        phamMembers = get_members_of_pham(c, phamName)
        phamMembers.remove(GeneID)
        for phamMember in phamMembers:
          if phamMember not in genes:
            continue
          print 'phamMember: %s' % phamMember
          relatives = [phamMember]
          #relatives = get_all_relatives(c, phamMember)
          #print 'seed: %s' % phamMember
          relatives = phamchecker.follow_rel_chain(c, phamMember, relatives, ignore=[GeneID])
          phamMembers.sort()
          relatives.sort()
          if relatives == phamMembers:
            # just remove this gene and others added later, as usual
            sqlQuery = "SELECT orderAdded from pham WHERE pham.GeneID = '%s'" % GeneID
            print sqlQuery
            try: c.execute(sqlQuery)
            except:
              print "'error executing sqlQuery: %s'" % sqlQuery
              c.execute("SHOW WARNINGS")
              errors = c.fetchall()
              for error in errors:
                print error

            o = c.fetchone()
            if o:
              o = str(int(o[0]))
              #sqlQuery = "DELETE from pham WHERE name = '%s' AND orderAdded >= '%s'" % (phamName, o)
              sqlQuery = "DELETE pham from pham, gene, phage WHERE pham.GeneID = gene.GeneID and gene.PhageID = phage.PhageID AND pham.name = '%s' AND orderAdded >= '%s'" % (phamName, o)
              print sqlQuery
              try: c.execute(sqlQuery)
              except:
                print "'error: %s'" % sqlQuery
                c.execute("SHOW WARNINGS")
                errors = c.fetchall()
                for error in errors:
                  print error
              print 'deleted', c.rowcount, 'rows from pham'
            else:
              print "Can't find the orderAdded for Gene: %s" % (GeneID)
              #sys.exit()
          if relatives != phamMembers:
            # move children from pham_old to pham
            print '*' * 600
            print 'moving children (%s) of %s from pham_old to pham' % (children, phamName)
            sqlQuery = "DELETE from pham WHERE pham.name = '%s'" % (phamName)
            try: c.execute(sqlQuery)
            except:
              print "'error: %s'" % sqlQuery
              c.execute("SHOW WARNINGS")
              errors = c.fetchall()
              for error in errors:
                print error
            c.execute("COMMIT")

            for child in children:
              print "CHILD: %s" % child
              sqlQuery = "INSERT INTO pham SELECT * from pham_old WHERE name = '%s'" % child
              try: c.execute(sqlQuery)
              except:
                print "'error: %s'" % sqlQuery
                c.execute("SHOW WARNINGS")
                errors = c.fetchall()
                for error in errors:
                  print error
              sqlQuery = "DELETE FROM pham_old WHERE name = '%s'" % child
              try:
                c.execute(sqlQuery)
                print 'deleted', c.rowcount, 'rows from pham_old'
              except:
                print "'error: %s'" % sqlQuery
                c.execute("SHOW WARNINGS")
                errors = c.fetchall()
                for error in errors:
                  print error
              c.execute("COMMIT")

    c.execute("DELETE gene_domain FROM gene, phage, gene_domain WHERE gene_domain.GeneID = gene.GeneID AND gene.PhageID = phage.PhageID AND phage.PhageID = '%s'" % PhageID)
    print 'deleted', c.rowcount, 'rows from gene_domain'
    c.execute("DELETE pham FROM pham, gene, phage WHERE pham.GeneID = gene.GeneID AND gene.PhageID = phage.PhageID AND phage.PhageID = '%s'" % PhageID)
    print 'deleted', c.rowcount, 'rows from pham'
    c.execute("DELETE pham_old FROM pham_old, gene, phage WHERE pham_old.GeneID = gene.GeneID AND gene.PhageID = phage.PhageID AND phage.PhageID = '%s'" % PhageID)
    print 'deleted', c.rowcount, 'rows from pham_old'

    #print 'genes in pham that should not be there: %s' % c.fetchall()
    c.execute("DELETE gene FROM gene, phage WHERE gene.PhageID = phage.PhageID AND phage.PhageID = '%s'" % PhageID)
    print 'deleted', c.rowcount, 'rows from gene'
    print 'deleted genes'
    c.execute("DELETE FROM phage WHERE PhageID = '%s'" % PhageID)
    print 'deleted', c.rowcount, 'rows from phage'
    print 'deleted phage'
    c.execute("COMMIT")
    print "PhageID '" + PhageID + "' has been successfully removed from the database."
    
def create_db(db_name=None, template=None, clone=False):
  '''Creates a new database from a .sql template using the supplied db_name as the database name'''

  #@db_name: name for new database
  #@template: filename for blank template, including path

  c = MySQLdb.connect(read_default_file="~/.my.cnf").cursor()
  c.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '%s'" % db_name)
  if c.rowcount != 0:
    print "can't create database '%s' because it already exists" % db_name
    return
  c.execute("CREATE DATABASE %s" % db_name)
  if template:
    os.system("mysql --defaults-file='~/.my.cnf' %s < %s" % (db_name, template))
  elif clone:
    import tempfile
    t = tempfile.mkstemp()
    print t
    print "mysqldump --defaults-file='~/.my.cnf' %s > %s" % (clone, t[1])
    os.system("mysqldump --defaults-file='~/.my.cnf' %s > %s" % (clone, t[1]))

    print "mysql --defaults-file='~/.my.cnf' %s < %s" % (db_name, t[1])
    os.system("mysql --defaults-file='~/.my.cnf' %s < %s" % (db_name, t[1]))
    os.close(t[0])
    os.remove(t[1])

def add_notes(c):
  '''adds notes to gene records if they are in the GenBank file'''
  phages = get_phages(c, PhageID=True)
  for PhageID in phages:
    c.execute("SELECT accession FROM phage WHERE PhageID = '%s' AND accession !=''" % PhageID)
    try:
      accession = c.fetchall()[0][0]
    except:
      pass
    print accession
    record = query_NCBI(accession)
    #print record
    #sys.exit()
    c.execute("LOCK TABLES gene WRITE")
    Accession = record.id
    for feature in record.features:
      #print feature
      name = None
      TypeID = feature.type
      if feature.type == 'source':
        ref = feature.qualifiers['db_xref'][0]
        PhageID = ref.split(':')[-1]
      elif feature.type == 'CDS':
        GeneID = None
        name = None
        exp = re.compile('^\d')
        if feature.qualifiers.has_key('locus_tag'):
          name = feature.qualifiers['locus_tag'][0]

        if feature.qualifiers.has_key('gene') and not name:
          if exp.match(feature.qualifiers['gene'][0]):
            pass
            #print "can't use 'locus_tag' because", feature.qualifiers['locus_tag'][0], "starts with a number"
          else:
            #print 'using locus_tag:', feature.qualifiers['locus_tag'][0]
            name = feature.qualifiers['locus_tag'][0]
        if feature.qualifiers.has_key('product') and not name:
          if exp.match(feature.qualifiers['product'][0]):
            pass
            #print "can't use 'product' because", feature.qualifiers['product'][0], "starts with a number"
          else:
            print 'using product:', feature.qualifiers['product'][0]
            name = feature.qualifiers['product'][0]
        if not name:
          if feature.qualifiers.has_key('standard_name'):
            name = feature.qualifiers['standard_name'][0]
            name = name.replace(" ", "")
        if not name:
          print "can't find a usable gene name...exiting"
          try:
            print feature.qualifiers
            #print "'locus_tag:'", feature.qualifiers['locus_tag'][0]
            #print "'product:'", feature.qualifiers['product'][0]
          except: pass
          c.execute("UNLOCK TABLES")
          sys.exit()

        if feature.qualifiers.has_key('db_xref'):
          xref = feature.qualifiers['db_xref']
          for ref in xref:
            if ref.find('GeneID') != -1:
              GeneID = ref.split(':')[-1]
              print 'found GeneID:', GeneID
            else:
              if name:
                GeneID = PhageID + '_' + name
   
        if feature.qualifiers.has_key('note'):
          note = feature.qualifiers['note'][0]
          note = note_filter(note)
          print "executing: UPDATE gene SET Notes = '%s' WHERE GeneID = '%s' AND Notes IS NULL" % (note, GeneID)
          c.execute("UPDATE gene SET Notes = '%s' WHERE GeneID = '%s' AND Notes IS NULL" % (note, GeneID))
          c.execute("COMMIT")
          # DO UPDATE HERE
    c.execute("UNLOCK TABLES")

def add_phage(record, c=None):
  '''Adds a phage to the phage table'''
  c.execute("LOCK TABLES phage WRITE")
  Accession = record.id
  Notes = record.description
  Sequence = record.seq.tostring()
  SequenceLength = len(Sequence)
  for feature in record.features:
    if feature.type == 'source':
      Name = None
      PhageID = None
      if feature.qualifiers.has_key('organism'):
        Name = feature.qualifiers['organism'][0].split(' ')[-1]
        #Name = feature.qualifiers['organism'][0].replace('Mycobacteriophage ','')
        PhageID = Name
      if feature.qualifiers.has_key('db_xref'):
        ref = feature.qualifiers['db_xref'][0]
        PhageID = ref.split(':')[-1]
      if not PhageID:
        print 'PhageID cannot be found.'
        print 'these are the feature qualifiers:', feature.qualifiers
        sys.exit()
      #print 'PhageID:', PhageID
      if feature.qualifiers.has_key('lab_host'):
        HostStrain = feature.qualifiers['lab_host'][0]
      elif feature.qualifiers.has_key('specific_host'):
        HostStrain = feature.qualifiers['specific_host'][0].replace("'","\\'")
      else:
        HostStrain = None
      if PhageID and not Name: Name = PhageID
      print Name
      phage = {'PhageID':PhageID, 'Accession':Accession, 'Name':Name, 'HostStrain':HostStrain, 'Sequence':Sequence, 'SequenceLength':SequenceLength, 'Notes':Notes}
      for key in phage.keys():
        if key != 'Sequence': print key, ':', phage[key]
      try:
        c.execute("""INSERT INTO phage (PhageID, Accession, Name, HostStrain, Sequence, SequenceLength, Notes) VALUES ('%(PhageID)s', '%(Accession)s', '%(Name)s', '%(HostStrain)s', '%(Sequence)s', '%(SequenceLength)s', '%(Notes)s')""" %phage)
        c.execute("UNLOCK TABLES")
        print 'added phage %s' % Name
        return PhageID
      except:
        print 'error inserting phage genome into phage table'
        c.execute("UNLOCK TABLES")
        return None

def name_filter(name):
  name = name.replace(' ','_')
  name = name.replace('!','_')
  name = name.replace('@','_')
  name = name.replace('#','_')
  name = name.replace('$','_')
  name = name.replace('%','_')
  name = name.replace('^','_')
  name = name.replace('&','_')
  name = name.replace('*','_')
  name = name.replace('(','_')
  name = name.replace(')','_')
  name = name.replace('~','_')
  name = name.replace('`','_')
  name = name.replace('{','_')
  name = name.replace('}','_')
  name = name.replace('[','_')
  name = name.replace(']','_')
  name = name.replace('.','_')
  name = name.replace(',','_')
  name = name.replace('<','_')
  name = name.replace('>','_')
  name = name.replace('?','_')
  name = name.replace('/','_')
  name = name.replace('-','_')
  name = name.replace('\'',' ')
  return name

def note_filter(note):
  '''note = note.replace('!','_')
  note = note.replace('@','_')
  note = note.replace('#','_')
  note = note.replace('$','_')
  note = note.replace('^','_')
  note = note.replace('&','_')
  note = note.replace('*','_')
  note = note.replace('(',' ')
  note = note.replace(')','_')
  note = note.replace('~','_')
  note = note.replace('`','_')
  note = note.replace('{','_')
  note = note.replace('}','_')
  note = note.replace('[','_')
  note = note.replace(']','_')
  #note = note.replace('.','_')
  note = note.replace(',','_')
  note = note.replace('<','_')
  note = note.replace('>','_')
  note = note.replace('?','_')
  note = note.replace('/','_')
  note = note.replace('-','_')
  note = note.replace('%','\%')
  '''
  note = note.replace('\'',' ')
  note = note.replace('\"',' ')
  return note

def check_record_for_problems(record):
  '''checks to make sure the GenBank file is valid before trying to add anything to the database'''
  print "CHECKING RECORD FOR PROBLEMS"
  print "-" * 80
  GeneIDs = []
  problems = []
  for feature in record.features:
    TypeID = feature.type
    if feature.type == 'source':
      try:
        if feature.qualifiers.has_key('organism'):
          #PhageID = feature.qualifiers['organism'][0].split(' ')[-1]
          Name = feature.qualifiers['organism'][0].replace('Mycobacteriophage ','')
          PhageID = Name

        else:
          ref = feature.qualifiers['db_xref'][0]
          PhageID = ref.split(':')[-1]
      except KeyError:
        error = 'this file lacks a %s entry in the GenBank file\n    Under source, a line should read like the following,\n\
    where \"phage name\" is replaced with the actual name of your phage:\n\
    /db_xref=\"taxon:phage name\"' % 'taxon'
        problems.append(error)
        print error
    elif feature.type == 'CDS':
      #print feature
      GeneID = None
      name = None
      s = t = translation = None

      exp = re.compile('^\d')

      if feature.qualifiers.has_key('db_xref'):
        xref = feature.qualifiers['db_xref']
        for ref in xref:
          if ref.find('GeneID') != -1:
            GeneID = ref.split(':')[-1]
            #print 'found GeneID:', GeneID
      
      if feature.qualifiers.has_key('gene'):
        name = feature.qualifiers['gene'][0]
        name = name_filter(name)

      if feature.qualifiers.has_key('locus_tag') and not name:
        if exp.match(feature.qualifiers['locus_tag'][0]):
          pass
          #print "can't use 'locus_tag' because", feature.qualifiers['locus_tag'][0], "starts with a number"
        else:
          #print 'using locus_tag:', feature.qualifiers['locus_tag'][0]
          name = feature.qualifiers['locus_tag'][0]
          name = name_filter(name)
      if feature.qualifiers.has_key('product') and not name:
        if exp.match(feature.qualifiers['product'][0]):
          pass
          #print "can't use 'product' because", feature.qualifiers['product'][0], "starts with a number"
        else:
          #print 'using product:', feature.qualifiers['product'][0]
          name = feature.qualifiers['product'][0]
          name = name_filter(name)
      if not name:
        error = "can't find a usable gene name"
        problems.append(error)
        print error
        print feature.qualifiers
      else: name = r"%s" % name.replace("'", "''")
      try: translation = feature.qualifiers['translation'][0]
      except KeyError:
        error = '%s from feature %s lacks a translation' % (name, feature)
        problems.append(error)
        print error

      if feature.strand == 1:
        orientation = 'F'
      elif feature.strand == -1:
        orientation = 'R'
      else:
        error = 'error determining gene orientation'
        problems.append(error)
        print error

      start, stop = feature.location.start.position, feature.location.end.position
      try:
        if start > stop:
          length = start - stop
        else:
          length = stop - start
      except:
        error = 'error calculating start and stop for Gene', name
        problems.append(error)
        print error
      if orientation == 'F':
        startCodon = record.seq[int(start):int(start)+3].tostring()
        stopCodon = record.seq[int(stop)-3:int(stop)].tostring()
        recordSeq = record.seq[int(start):int(stop)]
      else:
        stopCodon = record.seq[int(start):int(start)+3].reverse_complement().tostring()
        startCodon = record.seq[int(stop)-3:int(stop)].reverse_complement().tostring()
        recordSeq = record.seq[int(start):int(stop)].reverse_complement()

      if translation[-1] in ('*', 'Z'): translation = translation[:-1]

      bpTranslation = translate(recordSeq).tostring()
      try:
        if bpTranslation[-1] == '*': bpTranslation = bpTranslation[:-1]
        if bpTranslation[0] in ('L', 'V'): bpTranslation = 'M' + bpTranslation[1:]
      except:
        print bpTranslation
      if bpTranslation != translation:
        if bpTranslation.find('*') != -1 and translation.find('*') == -1: # this situation arises with programmed frameshifts
          pass
        else:
          error = 'translation for gene %s doesn\'t match a translation computed by Phamerator:\n\
>phamerator_%s\n%s\n>GenBank_%s\n%s' % (name, name, bpTranslation, name, translation)
          problems.append(error)
          print error

      if startCodon not in ['ATG', 'GTG', 'TTG']:
        s = Seq(startCodon)
        t = translate(s).tostring()
        error = "start codon for gene %s is '%s', which is not valid. ('%s' encodes residue '%s'.)" % (name, startCodon, startCodon, t)
        problems.append(error)
        print error
      if stopCodon not in ['TAA', 'TAG', 'TGA']:
        s = Seq(stopCodon)
        t = translate(s).tostring()
        error = "stop codon for gene %s is '%s', which is not valid. ('%s' encodes residue '%s'.)" % (name, stopCodon, stopCodon, t)
        problems.append(error)
        print error
  if problems: return problems
  else: return None

def add_genes(record, c=None):
  '''Adds genes from one phage genome to the gene table'''
  GeneIDs = []
  c.execute("LOCK TABLES gene WRITE")
  for feature in record.features:
    TypeID = feature.type
    if feature.type == 'source':
      if feature.qualifiers.has_key('db_xref'):
        ref = feature.qualifiers['db_xref'][0]
        PhageID = ref.split(':')[-1]
      elif feature.qualifiers.has_key('organism'):
        PhageID = feature.qualifiers['organism'][0].split(' ')[-1]
      else:
        print 'PhageID cannot be found.'
        print 'these are the feature qualifiers:', feature.qualifiers
        sys.exit()
    elif feature.type == 'CDS':
      GeneID = None
      name = None

      if feature.qualifiers.has_key('note'):
        note = feature.qualifiers['note'][0]
        note = note_filter(note)
      else: note = ""

      exp = re.compile('^\d')

      if feature.qualifiers.has_key('db_xref'):
        xref = feature.qualifiers['db_xref']
        for ref in xref:
          if ref.find('GeneID') != -1:
            GeneID = ref.split(':')[-1]

      if feature.qualifiers.has_key('locus_tag'):
        name = feature.qualifiers['locus_tag'][0]

      if feature.qualifiers.has_key('gene') and not name:
        if exp.match(feature.qualifiers['gene'][0]):
          pass
          #print "can't use 'locus_tag' because", feature.qualifiers['locus_tag'][0], "starts with a number"
        else:
          #print 'using locus_tag:', feature.qualifiers['locus_tag'][0]
          name = feature.qualifiers['locus_tag'][0]
      if feature.qualifiers.has_key('product') and not name:
        if exp.match(feature.qualifiers['product'][0]):
          pass
          #print "can't use 'product' because", feature.qualifiers['product'][0], "starts with a number"
        else:
          #print 'using product:', feature.qualifiers['product'][0]
          name = feature.qualifiers['product'][0]
      if not name:
        if feature.qualifiers.has_key('standard_name'):
          name = feature.qualifiers['standard_name'][0]
          name = name.replace(" ", "")
      if not name:
        print "can't find a usable gene name..."
        try:
          print "'locus_tag:'", feature.qualifiers['locus_tag'][0]
          print "'product:'", feature.qualifiers['product'][0]
        except: pass
        c.execute("UNLOCK TABLES")
        sys.exit()
      else: name = r"%s" % name.replace("'", "''")
      try: translation = feature.qualifiers['translation'][0]
      except KeyError:
        print 'this feature lacks a translation:'
        print 'offending feature\n', feature
        print 'exiting due to the above error'
        c.execute("ROLLBACK")
        sys.exit()
      
      if not GeneID:
        GeneID = PhageID + '_' + name
        #GeneID = name

      while GeneID in GeneIDs:
          GeneID = raw_input('GeneID %s is already in use.  Please specify a new GeneID: ' % GeneID)
      GeneIDs.append(GeneID)
      
      if feature.strand == 1:
        orientation = 'F'
      elif feature.strand == -1:
        orientation = 'R'
      else:
        print 'error determining gene orientation'
      start, stop = feature.location.start.position, feature.location.end.position
      try:
        if start > stop:
          length = start - stop
        else:
          length = stop - start
      except:
        print 'error calculating start and stop for Gene', name
        c.execute("UNLOCK TABLES")
        sys.exit()
      if orientation == 'F':
        startCodon = record.seq[int(start):int(start)+3].tostring()
        stopCodon = record.seq[int(stop)-3:int(stop)].tostring()
      else:
        stopCodon = record.seq[int(start):int(start)+3].reverse_complement().tostring()
        startCodon = record.seq[int(stop)-3:int(stop)].reverse_complement().tostring()
      if startCodon not in ['ATG', 'GTG', 'TTG']:
        print 'error with start codon'
        print "start:", startCodon
      if stopCodon not in ['TAA', 'TAG', 'TGA']:
        print 'error with stop codon'
      gene = {'GeneID':GeneID, 'PhageID':PhageID, 'Notes':note, 'Start':start, 'Stop':stop, 'Length':length, 'Translation':translation, 'StartCodon':startCodon, 'StopCodon':stopCodon, 'Name':name, 'TypeID': TypeID, 'Orientation':orientation}
      sqlQuery = """INSERT INTO gene (GeneID, PhageID, Notes, Start, Stop, Length, Translation, StartCodon, StopCodon, Name, TypeID, Orientation) VALUES ('%(GeneID)s', '%(PhageID)s', '%(Notes)s', '%(Start)s', '%(Stop)s', '%(Length)s', '%(Translation)s', '%(StartCodon)s', '%(StopCodon)s', '%(Name)s', '%(TypeID)s', '%(Orientation)s')""" %gene
      try:
        c.execute(sqlQuery)
      except:
        print sqlQuery
        print "Unexpected error:", sys.exc_info()[0]
        print "bailing..."
        sys.exit()
  c.execute("UNLOCK TABLES")

def query_NCBI(query):
  '''Submits a query to NCBI's Genbank for a phage genome'''
  gi_list = GenBank.search_for(query + " AND Hatfull GF[AUTH] srcdb_refseq[prop]")
  if len(gi_list) != 0:
    print 'found RefSeq GenBank entry'
  else:
    gi_list = GenBank.search_for(query + " AND Hatfull GF[AUTH]")

  if len(gi_list) == 0:
    gi_list = GenBank.search_for(query)
  if len(gi_list) == 0:
    print 'no results found'
    return
  elif len(gi_list) > 1:
    selection = 0
    for i in range(len(gi_list)):
      print i+1, '\t', gi_list[i]
    selection = raw_input("Your search returned multiple results.  Please type the number for your selection: ")
    selection = int(selection) - 1
  else:
    selection = 0
    
  #feature_parser = GenBank.FeatureParser()
  #ncbi_dict = GenBank.NCBIDictionary('nucleotide', 'genbank', parser = feature_parser)
  #gb_seqrecord = ncbi_dict[gi_list[selection]]
  #return gb_seqrecord
  from Bio import Entrez, SeqIO
  handle = Entrez.efetch(db='nucleotide', id=result, rettype='gb')
  return SeqIO.read(handle, 'genbank')

def parse_GenBank_file(gb_file):
  '''Parses a GenBank file using the Biopython.GenBank parser'''
  if not os.path.isfile(gb_file):
    print filename, 'not found.  Exiting...'
    sys.exit()
  gb_handle = open(gb_file, 'rU')
  feature_parser = GenBank.FeatureParser()
  gb_iterator = GenBank.Iterator(gb_handle, feature_parser)
  #gb_seqrecord = gb_iterator.next()
  gb_seqrecord = SeqIO.read(gb_handle, "genbank")
  return gb_seqrecord

def get_phages(c, PhageID=None, name=None):
  '''Gets phages from the phage table'''
  if PhageID and not name: SQLquery = "SELECT PhageID FROM phage ORDER BY cluster"
  elif name and not PhageID: SQLquery = "SELECT name FROM phage ORDER BY cluster"
  elif PhageID and name: SQLquery = "SELECT PhageID, name FROM phage ORDER BY cluster"
  else: return None
  try:
    c.execute(SQLquery)
  except:
    return []
  results = c.fetchall()
  returnData = []
  for result in results:
    if len(result) == 1: returnData.append(result[0])
    else: returnData.append(result)
  #print 'returnData:', returnData
  return returnData

def get_number_of_genomes(c):
  '''returns the number of genomes in the database'''
  sqlQuery = "select count(*) from phage"
  c.execute(sqlQuery)
  r = c.fetchall()
  return r[0][0]

def get_number_of_phamilies(c):
  '''returns the number of phamilies in the database'''
  sqlQuery = "select distinct(name) from pham"
  c.execute(sqlQuery)
  return c.rowcount

def get_number_of_genes(c, PhageID=None, name=None):
  '''returns the number of genes in a given phage genome'''
  if PhageID:
    sqlQuery = "select count(*) from gene,phage where gene.PhageID='%s' and gene.PhageID = phage.PhageID" % PhageID
  elif name:
    sqlQuery = "select count(*) from gene,phage where phage.name = '%s' and gene.PhageID = phage.PhageID" % name
  else:
    sqlQuery = "select count(*) from gene"
  c.execute(sqlQuery)
  r = c.fetchall()
  return r[0][0]

def get_shortest_genome(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select name, sequenceLength from phage order by sequenceLength asc limit 1"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r

def get_longest_genome(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select name, sequenceLength from phage order by sequenceLength desc limit 1"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r

def get_mean_genome_length(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select AVG(sequenceLength) from phage"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r[0]

def get_shortest_gene(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select phage.name, gene.name, gene.length from gene, phage where gene.PhageID = phage.PhageID order by length asc"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r

def get_longest_gene(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select phage.name, gene.name, length(translation)*3 from gene, phage where length(translation) and gene.PhageID = phage.PhageID order by length(translation) desc limit 1;"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r

def get_mean_gene_length(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  sqlQuery = "select AVG(length) from gene"
  c.execute(sqlQuery)
  r = c.fetchone()
  return r[0]

def get_smallest_pham_size(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  phamNames = get_pham_names(c)
  phamSizeDict = {}
  for pham in phamNames:
    phamSizeDict[pham] = get_number_of_pham_members(c, pham)
  sizeSorted = sorted(phamSizeDict.iteritems(), key=lambda (k,v): (v,k))
  minSize = sizeSorted[0][1]
  minPhams = []
  for k, v in sizeSorted:
    if v == minSize:
      minPhams.append(k)
  # return tuple (list of name of smallest phams, size)
  return (minPhams, minSize)

def get_largest_pham_size(c):
  '''returns a tuple containing the name of the largest pham and its length'''
  phamNames = get_pham_names(c)
  phamSizeDict = {}
  for pham in phamNames:
    phamSizeDict[pham] = get_number_of_pham_members(c, pham)
  sizeSorted = sorted(phamSizeDict.iteritems(), key=lambda (k,v): (v,k), reverse=True)
  maxSize = sizeSorted[0][1]
  maxPhams = []
  for k, v in sizeSorted:
    if v == maxSize:
      maxPhams.append(k)
  # return tuple (list of name of largest phams, size)
  return (maxPhams, maxSize)

def get_mean_pham_size(c):
  '''returns a tuple containing the name of the longest genome and its length'''
  phamNames = get_pham_names(c)
  phamSize = []
  for pham in phamNames:
    phamSize.append(get_number_of_pham_members(c, pham))
  return sum(phamSize)/float(len(phamSize))

def get_mean_translation_size_for_pham(c, phamName):
  '''returns the mean size of the proteins in the given pham'''
  sqlQuery = "select pham.name, AVG(length(translation)) from gene, pham where gene.GeneID = pham.GeneID and pham.name = '%s' group by pham.name" % phamName
  try:
    c.execute(sqlQuery)
    return c.fetchone()[1]
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_mean_translation_size_for_all_phams(c):
  '''returns the mean size of the proteins in the given pham'''
  sqlQuery = "select pham.name, AVG(length(translation)) from gene, pham where gene.GeneID = pham.GeneID group by pham.name"
  try:
    c.execute(sqlQuery)
    r = c.fetchall()
    translations = {}
    for pham in r:
      translations[int(pham[0])] = float(pham[1])
    return translations
      
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error
    
def get_genome_length(c, PhageID=None, name=None):
  '''returns the length of the specified genome'''
  if PhageID:
    sqlQuery = "select sequenceLength from phage where PhageID='%s'" % PhageID
  elif name:
    sqlQuery = "select sequenceLength from phage where name='%s'" % name
  else:
    print "You didn't specify a PhageID or name for your phage.  Exiting..."
    sys.exit()
  c.execute(sqlQuery)
  r = c.fetchall()
  length = r[0][0]
  return length

def get_clusters(c, include_unclustered=False):
  '''returns the names of all the clusters'''
  sqlQuery = "SELECT DISTINCT cluster from phage WHERE cluster IS NOT NULL ORDER BY cluster"
  try:
    c.execute(sqlQuery)
    clusters = list()
    for i in c.fetchall():
      if not i: continue # don't return unclustered phages
      clusters.append(i[0])
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

  if include_unclustered == False:
    return clusters
  sqlQuery = "SELECT name from phage WHERE cluster IS NULL ORDER BY name"
  try:
    c.execute(sqlQuery)
    unclustered = list()
    for i in c.fetchall():
      if not i: continue # don't return unclustered phages
      unclustered.append(i[0])
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error
  return clusters + unclustered

def get_clusters_from_pham(c, phamName, db=None):
  '''returns a list of the cluster(s) containing a phage with a member of the given pham'''

  if os.path.exists('/tmp/%s/%s/phams/%s/clusters' % (os.environ['USER'], db, phamName)) \
    and os.path.exists('/tmp/%s/%s/phams/%s/unclustered' % (os.environ['USER'], db, phamName)):
    pkl_file = open('/tmp/%s/%s/phams/%s/clusters' % (os.environ['USER'], db, phamName), 'rb')
    clusters = pickle.load(pkl_file)
    pkl_file.close()
    pkl_file = open('/tmp/%s/%s/phams/%s/unclustered' % (os.environ['USER'], db, phamName), 'rb')
    unclustered = pickle.load(pkl_file)
    pkl_file.close()
    
  else:
    PhageIDs = get_PhageID_members_of_pham(c, phamName)
    clusters = []
    unclustered = []
    for PhageID in PhageIDs:
      cluster = get_cluster_from_PhageID(c, PhageID)
      # for unclustered phages, add the phage's name instead of 'None'
      if not cluster: unclustered.append(get_phage_name_from_PhageID(c, PhageID))
      elif cluster and cluster not in clusters:
        clusters.append(cluster)
    clusters.sort() 
    unclustered.sort()
    if not os.path.exists('/tmp/%s/%s/' % (os.environ['USER'], db)):
      os.mkdir('/tmp/%s/%s/' % (os.environ['USER'], db))
    if not os.path.exists('/tmp/%s/%s/phams/' % (os.environ['USER'], db)):
      os.mkdir('/tmp/%s/%s/phams/' % (os.environ['USER'], db))
    if not os.path.exists('/tmp/%s/%s/phams/%s' % (os.environ['USER'], db, phamName)):
      os.mkdir('/tmp/%s/%s/phams/%s' % (os.environ['USER'], db, phamName))
    if not os.path.exists('/tmp/%s/%s/phams/%s/clusters' % (os.environ['USER'], db, phamName)):
      output = open('/tmp/%s/%s/phams/%s/clusters' % (os.environ['USER'], db, phamName), 'wb')
      pickle.dump(clusters, output)
      output.close()
    if not os.path.exists('/tmp/%s/%s/phams/%s/unclustered' % (os.environ['USER'], db, phamName)):
      output = open('/tmp/%s/%s/phams/%s/unclustered' % (os.environ['USER'], db, phamName), 'wb')
      pickle.dump(unclustered, output)
      output.close()

  return clusters, unclustered

def get_cluster_from_PhageID(c, PhageID):
  '''returns the cluster for a specified PhageID'''
  try:
    sqlQuery = "select cluster from phage where PhageID = '%s'" % PhageID
    c.execute(sqlQuery)
    r = c.fetchall()
    if r[0][0]:
      return r[0][0]
  except:
    pass
    
def get_PhageIDs_from_cluster(c, cluster):
  '''returns a list of the PhageIDs for the phages in the given cluster'''
  try:
    sqlQuery = "select PhageID from phage where cluster LIKE '%s%%'" % cluster
    c.execute(sqlQuery)
    results = c.fetchall()
    p = []
    for r in results: p.append(r[0])
    return p
  except:
    pass   
    
def get_gene_percent_GC(c, GeneID=None):
  '''returns the GC% for a specified gene'''
  seq = get_seq_from_GeneID(c, GeneID)
  if not seq: return -1
  return calculate_GC(seq)
  
def get_percent_GC(c, PhageID=None, name=None):
  '''returns the GC% for a specified phage genome'''
  try:
    if PhageID:
      sqlQuery = "select GC from phage where PhageID='%s'" % PhageID
    elif name:
      sqlQuery = "select GC from phage where name='%s'" % name
    else:
      print "You didn't specify a PhageID or name for your phage.  Exiting..."
    c.execute(sqlQuery)
    r = c.fetchall()
    if r[0][0]:
      return float(r[0][0])
  except: pass
  if PhageID:
    sqlQuery = "select sequence, sequenceLength from phage where PhageID='%s'" % PhageID
  elif name:
    sqlQuery = "select sequence, sequenceLength from phage where name='%s'" % name
  else:
    print "You didn't specify a PhageID or name for your phage.  Exiting..."
    sys.exit()
  c.execute(sqlQuery)
  r = c.fetchall()
  #print 'r:', r
  #print 'r:', len(r)
  seq, length = r[0][0], r[0][1]
  #print 'seq: %s, length: %s' % (seq, length)
  return calculate_GC(seq)

def calculate_GC(seq):
  length = len(seq)
  GC = 0
  for s in seq:
    if s.upper() == 'C' or s.upper() == 'G':
      GC += 1
  return (GC/float(length)) * 100

def phages_have_changed(old, new):
  '''Checks for differences between two lists of PhageIDs'''
  for phage in old:
    if phage not in new: return True
  for phage in new:
    if phage not in old: return True
  return False

def signal_handler(signal, frame):
  '''Warns user not to kill the program when database operations are underway'''
  print '*'*36, 'WARNING', '*'* 35
  print 'Closing this applicaiton now could leave the database in a non-recoverable, inconsistent state!'
  proceed = raw_input('Are you sure you want to do this? [y/N]:').upper()
  if proceed == 'Y':
    confirm = raw_input('Really [y/N]:').upper()
    if confirm == 'Y':
      print 'Rolling back changes...'
      try: c.execute("ROLLBACK")
      except:
        c.execute("SHOW WARNINGS")
        errors = c.fetchall()
        for error in errors: print error
      print 'Program will exit when database operations complete'
      sys.exit()
  print 'Cancel request aborted.'

def get_length_of_genome(c, PhageID):
  '''returns the length of a genome'''
  sqlQuery = "SELECT SequenceLength FROM phage WHERE PhageID = '%s'" % PhageID
  try:
    c.execute(sqlQuery)
    result = c.fetchone()
    return result[0]
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_description_from_GeneID(c, GeneID):
  '''returns the text from the /notes entry in the original GenBank file'''
  sqlQuery = "SELECT notes FROM gene WHERE GeneID = '%s'" % GeneID
  #print 'getting note for %s' % (GeneID,)
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    return results[0]
  except:
    c.execute('SHOW WARNINGS')
    errors = c.fetchall()
    for error in errors: print error

def get_phage_name_from_PhageID(c, PhageID):
  '''Returns the name of a phage that corresponds to the given PhageID'''
  sqlQuery = "SELECT name FROM phage WHERE PhageID = '%s'" % PhageID
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    return results[0]
  except:
    c.execute('SHOW WARNINGS')
    errors = c.fetchall()
    for error in errors: print error

def get_PhageID_from_GeneID(c, GeneID):
  '''Returns the PhageID of a phage whose genome contains the given GeneID'''
  sqlQuery = "SELECT PhageID FROM gene WHERE GeneID = '%s'" % GeneID
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    return results[0]
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error
    
def get_PhageIDs(c):
  '''Returns a list of all PhageIDs in the database'''
  sqlQuery = "SELECT PhageID FROM phage"
  try:
    c.execute(sqlQuery)
    results = c.fetchall()
    p = []
    for r in results: p.append(r[0])
    return p
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_phage_name_from_GeneID(c, GeneID):
  '''Returns the name of the phage that contains a gene with the given GeneID'''
  sqlQuery = "SELECT phage.name FROM phage, gene WHERE GeneID = '%s' AND gene.PhageID = phage.PhageID" % GeneID
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    return results[0]
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_gene_number_from_GeneID(c, GeneID):
  """Returns the number of a given gene, without the phage name or 'gp'"""
  name = get_gene_name_from_GeneID(c, GeneID)
  exp = re.compile('\d+$')
  name = int(exp.search(name).group().strip())
  return name

def get_gene_name_from_GeneID(c, GeneID):
  '''Returns a gene name based on its GeneID'''
  sqlQuery = "SELECT name FROM gene WHERE GeneID = '%s'" % GeneID
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    name = results[0]
    name = name.split('_')[-1]
    return name
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_gene_start_stop_length_orientation_from_GeneID(c, GeneID):
  '''returns a tuple containing the start position, stop position, and length of a given gene'''
  sqlQuery = "SELECT Start, Stop, Length, orientation FROM gene WHERE GeneID = '%s'" % GeneID
  try:
    c.execute(sqlQuery)
    startStopLengthOrientation = c.fetchone()
    return startStopLengthOrientation
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_name_from_PhageID(c, PhageID):
  '''Retrieves a name from the phage table using the PhageID'''
  sqlQuery = "SELECT name FROM phage WHERE PhageID = '%s'" % PhageID
  try:
    c.execute(sqlQuery)
    results = c.fetchone()
    return results[0]
  except:
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors: print error

def get_PhageID_from_name(c, name):
  '''Retrieves a PhageID from the phage table using the phage name'''
  sqlQuery = "SELECT PhageID, name FROM phage WHERE name = '%s'" % name
  c.execute(sqlQuery)
  if c.rowcount != 1:
    sqlQuery = "SELECT PhageID, name FROM phage WHERE name LIKE '%s'" % name
    c.execute(sqlQuery)

  if c.rowcount == 1:
    #print 'found exact match'
    results = c.fetchall()
  else:
    sqlQuery = "SELECT PhageID, name FROM phage WHERE name LIKE '%" + name + "%'"
    c.execute(sqlQuery)
    results = c.fetchall()
 
  if len(results) < 1: print "Phage '" + name + "' was not found in the database."
  elif len(results) > 1:
    print "Multiple phages match the name you gave.  Please retry with one of the following names:"
    for result in results: print result[1]
  else: return results[0][0]

def get_phams(c):
  '''Retrieves a list of phams from the database'''
  sqlQuery = "SELECT name, GeneID FROM pham ORDER BY name"
  c.execute(sqlQuery)
  results = c.fetchall()
  str_results = []
  for i in results: str_results.append((str(i[0]),i[1]))
  return str_results

def get_pham_names(c):
  sqlQuery = "SELECT DISTINCT name FROM pham"
  c.execute(sqlQuery)
  results = c.fetchall()
  return results

def get_number_of_pham_members(c, phamName, PhageID=None, db=None):
  '''returns an int that is the number of members of a pham, or None if the pham does not exist. If specified only report members from given genome'''
  if PhageID:
    print 'using phageid %s' % PhageID
    sqlQuery = "SELECT COUNT(*) FROM pham, gene, phage WHERE pham.name = '%s' AND phage.PhageID = '%s' AND pham.GeneID = gene.GeneID and gene.PhageID = phage.PhageID" % (phamName, PhageID)
    c.execute(sqlQuery)
    count = c.fetchone()[0]
    return count
    
  if os.path.exists('/tmp/%s/%s/phams/%s/size' % (os.environ['USER'], db, phamName)):
    pkl_file = open('/tmp/%s/%s/phams/%s/size' % (os.environ['USER'], db, phamName), 'rb')
    size = pickle.load(pkl_file)
    print 'using cached size %s' % size
    pkl_file.close()
    return size
  else:
    #try:
    sqlQuery = "SELECT COUNT(*) FROM pham WHERE pham.name = '%s'" % phamName
    c.execute(sqlQuery)
    count = c.fetchone()[0]
    if not os.path.exists('/tmp/%s/' % (os.environ['USER'])):
      os.mkdir('/tmp/%s/' % (os.environ['USER']))
    if not os.path.exists('/tmp/%s/%s' % (os.environ['USER'], db)):
      os.mkdir('/tmp/%s/%s' % (os.environ['USER'], db))
    if not os.path.exists('/tmp/%s/%s/phams/' % (os.environ['USER'], db)):
      os.mkdir('/tmp/%s/%s/phams' % (os.environ['USER'], db))
    if not os.path.exists('/tmp/%s/%s/phams/%s' % (os.environ['USER'], db, phamName)):
      os.mkdir('/tmp/%s/%s/phams/%  s' % (os.environ['USER'], db, phamName))
    output = open('/tmp/%s/%s/phams/%s/size' % (os.environ['USER'], db, phamName), 'wb')
    print 'caching size %s for pham %s' % (count, phamName)
    pickle.dump(count, output)
    output.close()
    return count
    #except:
    #  print sqlQuery
    #  sys.exit()

def get_translation_from_GeneID(c, GeneID):
  '''returns a translated sequence from a GeneID'''
  sqlQuery = "SELECT translation FROM gene WHERE GeneID = '%s'" % GeneID
  c.execute(sqlQuery)
  return c.fetchone()[0]

def get_translation_from_id(c, id):
  '''returns a translated sequence from an id'''
  sqlQuery = "SELECT translation FROM gene WHERE id = '%s'" % id
  c.execute(sqlQuery)
  return c.fetchone()[0]

def get_GeneID_from_id(c, id):
  '''returns a translated sequence from a GeneID'''
  sqlQuery = "SELECT GeneID FROM gene WHERE id = '%s'" % id
  c.execute(sqlQuery)
  return c.fetchone()[0]

def get_translation_from_PhageID(c, PhageID):
  '''returns a translated sequence from a GeneID'''
  sqlQuery = "SELECT translation FROM gene WHERE GeneID = '%s'" % PhageID
  c.execute(sqlQuery)
  return c.fetchone()[0]


def get_domain_hits_from_GeneID(c, GeneID):
  '''returns the domain hit_id for a GeneID'''
  sqlQuery = "select domain.hit_id, gene_domain.query_start, gene_domain.query_end, gene_domain.expect, domain.description from domain, gene_domain, gene where domain.hit_id = gene_domain.hit_id and gene_domain.GeneID = gene.GeneID and gene.GeneID = '%s'" % GeneID
  #print sqlQuery
  c.execute(sqlQuery)
  d = c.fetchall()
  #if d: print d
  domains = []
  for domain in d:
    domains.append({'hit_id': domain[0], 'start': domain[1], 'end': domain[2], 'expect':domain[3], 'description':domain[4]})
  return domains
  
def get_domain_description_from_hit_id(c, hit_id):
  '''returns the domain description for a hit_id'''
  sqlQuery = "select domain.description from domain where domain.hit_id = '%s'"
  c.execute(sqlQuery)
  return c.fetchone()[0]

def get_seq_from_GeneID(c, GeneID, extra=None):
  '''returns the nucleotide sequence for a gene'''
  print 'getting sequence for gene %s' % GeneID
  sqlQuery = "SELECT start, stop, orientation, sequence FROM gene, phage WHERE gene.PhageID = phage.PhageID AND GeneID = '%s'" % GeneID
  c.execute(sqlQuery)
  start, stop, orientation, sequence = c.fetchone()
  if extra:
    start = start - extra
    stop = stop + extra
  #print 'start:', start, 'stop:', stop, 'seq:', sequence[start:stop].tostring()
  #print sequence[start:stop]
  if orientation == 'R':
    temp = list(sequence[start:stop])
    sequence = ''
    mapping = {'A':'T','C':'G','G':'C','T':'A', 'N':'N'}
    while 1:
      try: nt = temp.pop()
      except: break
      try: sequence = sequence + mapping[nt]
      except: print '%s is not a valid base code' % nt
    #print 'sequence: %s' % sequence
    return sequence
  #print 'sequence: %s' % sequence
  #return sequence[start:stop].tostring()
  return sequence[start:stop]

def get_seq_from_PhageID(c, PhageID):
  '''returns the nucleotide sequence for a genome'''
  sqlQuery = "SELECT sequence FROM phage WHERE PhageID = '%s'" % PhageID
  c.execute(sqlQuery)
  seq = c.fetchone()[0]
  return seq

def get_members_of_pham(c, phamName):
  '''returns a list of GeneIDs that are in the requested pham'''
  #print 'phamName: %s' % phamName
  sqlQuery = "SELECT GeneID FROM pham WHERE name = %s" % phamName
  c.execute(sqlQuery)
  GeneIDs = []
  for tuple in c.fetchall(): GeneIDs.append(tuple[0])
  return GeneIDs

def get_PhageID_members_of_pham(c, phamName):
  '''returns a list of PhageIDs for phages that have members of the request pham'''
  if not phamName: return []
  GeneIDs = get_members_of_pham(c, phamName)
  PhageIDs = []
  for GeneID in GeneIDs:
    PhageID = get_PhageID_from_GeneID(c, GeneID)
    if PhageID not in PhageIDs: PhageIDs.append(PhageID)
  return PhageIDs

def get_pham_from_GeneID(c, GeneID):
  '''returns an integer that is the pham that a given gene is in'''
  sqlQuery = "SELECT pham.name FROM pham, gene WHERE pham.GeneID = '%s' AND pham.GeneID = gene.GeneID" % GeneID
  c.execute(sqlQuery)
  try: pham = c.fetchone()[0]
  except: pham = None
  return pham

def do_blast_search(c, query):
  import shutil
  from Bio.Blast import NCBIStandalone
  from Bio.Blast import NCBIXML

  '''performs a blast search with the given query and returns a dict of results'''
  blastDbDirectory='/tmp/BLAST'
  cfg = ConfigParser.RawConfigParser()
  cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
  try:
    blastRootDirectory = cfg.get('Phamerator','blast_bin_dir')
  except ConfigParser.NoOptionError:
    try:
      blastRootDirectory = os.path.join(cfg.get('Phamerator', 'blast_dir'), 'bin')
    except ConfigParser.NoOptionError:
      blastRootDirectory = None
  if not os.path.isdir(blastDbDirectory):
    print "making directory '%s'" % blastDbDirectory
    os.mkdir(blastDbDirectory)
  if not os.path.exists(os.path.join(blastDbDirectory, 'formatdb')):
    if not os.path.exists(os.path.join(blastRootDirectory, 'formatdb')):
      print "can't find formatdb!"
      return None
    shutil.copy(os.path.join(blastRootDirectory,'formatdb'), blastDbDirectory)
    print "copying 'formatdb' to '%s'" % blastDbDirectory

  blast_db = os.path.join('/tmp/BLAST', 'blastDB.fasta')
  f = open(blast_db, 'w')
  f.write(get_fasta_aa(c))
  f.close()
  blast_file = os.path.join(blastRootDirectory, 'filetoblast.txt')
  f = open(blast_file, 'w')
  f.write('>%s\n%s' % (query, get_translation_from_GeneID(c, query)))
  f.close()
  os.system(os.path.join(blastDbDirectory, 'formatdb') + ' -i ' + os.path.join(blastDbDirectory, 'blastDB.fasta -o T'))
  print 'path to filetoblast.txt:', blast_file
  if sys.platform == 'win32':
    blastall_name = 'Blastall.exe'
    blast_exe = os.path.join(blastRootDirectory, blastall_name)
  else:
    blastall_name = 'blastall'
    blast_exe = os.path.join(blastRootDirectory, blastall_name)
  if sys.platform == 'win32':
     import win32api
     blast_db = win32api.GetShortPathName(blast_db)
     blast_file = win32api.GetShortPathName(blast_file)
     blast_exe = win32api.GetShortPathName(blast_exe)
  blast_out, error_info = NCBIStandalone.blastall(blast_exe, 'blastp', blast_db, blast_file, expectation=100, align_view=7)
  blast_records = NCBIXML.parse(blast_out)
  #print 'got iterator'
  results = {}
  recordnumber = 0
  nonmatchingQueries = []
  while 1:
    recordnumber += 1
    try: b_record = blast_records.next()
    except StopIteration: break

    if not b_record:
      continue
    print 'query:', b_record.query
    e_value_thresh = 100
    significant = False
    for alignment in b_record.alignments:
      bestHsp = None
      for hsp in alignment.hsps:
        if not bestHsp: bestHsp = hsp.expect
        elif bestHsp <= hsp.expect: continue
        if hsp.expect < e_value_thresh:
          alignment.title = alignment.title.replace(">","")
          if b_record.query != alignment.accession:
            significant = True
            #print 'adding', b_record.query, 'and', alignment.accession, 'to matches (score:',hsp.expect,')'
            results[alignment.accession] = hsp.expect
  return results

def do_pairwise_alignment(c, query, subject):
  '''performs a clustalw alignment and returns the percent identity'''
  print 'aligning %s:%s' % (query, subject)
  querySeq = get_translation_from_GeneID(c, query)
  subjectSeq = get_translation_from_GeneID(c, subject)
  f = open(os.path.join('/tmp', 'temp' + '.fasta'), 'w')
  f.write('>' + 'a' + '\n' + querySeq + '\n>' + 'b' + '\n' + subjectSeq + '\n')
  f.close()
  output_path = os.path.join('/tmp', 'temp' + '.aln')
  #cline = ClustalwCommandline(os.path.join('/tmp', 'temp' + '.fasta'))
  cline = ClustalwCommandline("clustalw", infile=os.path.join('/tmp', 'temp' + '.fasta'), outfile=output_path)
  #cline.set_output(os.path.join('/tmp', 'temp' + '.aln'))
  cline()
  
  alignment = AlignIO.read(output_path, "clustal")
  
  
  length = alignment.get_alignment_length()
  star = alignment._star_info.count('*')
  score = float(star)/length
  return score
  
def get_GeneIDs(c, type=None, PhageID=None):
  '''returns all GeneIDs in the database, or optionally only those of the specified type or belonging to the specified PhageID'''
  sqlQuery = ''
  if type:
    sqlQuery = "SELECT GeneID FROM gene WHERE TypeID = '%s'" % type
    if PhageID: sqlQuery += " AND PhageID = '%s'" % PhageID
  else:
    sqlQuery = "SELECT GeneID FROM gene"
    if PhageID: sqlQuery += " WHERE PhageID = '%s'" % PhageID
  
  c.execute(sqlQuery)
  results = c.fetchall()
  GeneIDs = []
  for r in results:
    GeneIDs.append(r[0])
  return GeneIDs

def get_genes_from_PhageID(c, PhageID):
  '''returns a list of GeneIDs that are in the requested phage'''
  sqlQuery = "SELECT GeneID FROM gene WHERE PhageID = '%s'" % PhageID
  sqlQuery = "SELECT GeneID from gene WHERE PhageID = '%s' ORDER BY PhageID, Start" % PhageID
  c.execute(sqlQuery)
  genes = c.fetchall()
  GeneIDs = []
  for g in genes: GeneIDs.append(g[0])
  return GeneIDs 

def get_fasta_aa(c, PhageIDs=None, include_drafts=False):
  '''returns a fasta formatted string of all proteins in the database'''
  if include_drafts:
    drafts = []
    for x in PhageIDs:
      if not x.endswith('-DRAFT') and not x.endswith('_Draft') and not x.endswith('-Draft') and not x.endswith('_DRAFT'):
        drafts.append(x + '-DRAFT')
        drafts.append(x + '_Draft')
        drafts.append(x + '-Draft')
        drafts.append(x + '_DRAFT')
  if PhageIDs:
    sqlQuery = "SELECT phage.name, gene.GeneID, gene.translation FROM phage, gene WHERE phage.PhageID = gene.PhageID AND phage.PhageID IN %s" % (tuple(PhageIDs+drafts),)
    print sqlQuery
  else:
    sqlQuery = "SELECT phage.name, gene.GeneID, gene.translation FROM phage, gene WHERE phage.PhageID = gene.PhageID"
  c.execute(sqlQuery)
  fasta = ''
  genes = c.fetchall()
  for g in genes: fasta = fasta + '>%s:%s\n%s\n' % (g[0], g[1], g[2])
  return fasta

def get_all_scores(c, alignmentType='both'):
  if alignmentType == 'clustalw':
  # I might not need the "query.type = 'Q' AND subject.type = 'S'" in the next SQL statement
    c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s""" % (GeneID, GeneID, self.clustalwThreshold))
  elif alignmentType == 'blast':
    c.execute("""SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s""" % (GeneID, GeneID, self.blastThreshold))
  elif alignmentType == 'both':
    c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s UNION SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s""" % (GeneID, GeneID, self.clustalwThreshold, GeneID, GeneID, self.blastThreshold))
  else:
    raise AlignmentTypeException

def get_relatives(c, GeneID, alignmentType='both', blastThreshold=None, clustalwThreshold=None):
  '''returns a list of GeneIDs that are related to the given gene'''
  if alignmentType == 'clustalw':
  # I might not need the "query.type = 'Q' AND subject.type = 'S'" in the next SQL statement
    c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s""" % (GeneID, GeneID, clustalwThreshold))
  elif alignmentType == 'blast':
    c.execute("""SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s""" % (GeneID, GeneID, blastThreshold))
  elif alignmentType == 'both':
    c.execute("""SELECT query.GeneID, subject.GeneID, clustalw.score FROM alignment AS query, alignment AS subject, clustalw WHERE clustalw.id = query.clustalw_id AND clustalw.id = subject.clustalw_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND clustalw.score >= %s UNION SELECT query.GeneID, subject.GeneID, blast.score FROM alignment AS query, alignment AS subject, blast WHERE query.blast_id = subject.blast_id AND blast.id = query.blast_id AND blast.id = subject.blast_id AND query.type = 'Q' AND subject.type = 'S' AND (query.GeneID = '%s' OR subject.GeneID = '%s') AND blast.score <= %s;""" % (GeneID, GeneID, clustalwThreshold, GeneID, GeneID, blastThreshold))
  else:
    raise AlignmentTypeException
  alignments = c.fetchall()
  return alignments

def get_pham_scores(c, GeneID):
  '''returns a tuple of tuples, each containing the clustalw and blast scores for the specified gene, using scores_summary'''
  clustalwScores = []
  blastScores = []
  sqlQuery = "SELECT query, subject, clustalw_score FROM scores_summary WHERE query = '%s' AND clustalw_score IS NOT NULL ORDER BY clustalw_score DESC" % GeneID
  c.execute(sqlQuery)
  cs = c.fetchall()
  if len(cs) > 0:
    for row in cs:
      query, subject, clustalw_score = row
      clustalwScore = (query, subject, float(clustalw_score))
      clustalwScores.append(clustalwScore)

  sqlQuery = "select query, subject, min(blast_score) from scores_summary where blast_score IS NOT NULL AND query = '%s' group by query, subject" % GeneID
  #sqlQuery = "SELECT query, subject, blast_score FROM scores_summary WHERE query = '%s' OR subject = '%s' AND blast_score IS NOT NULL" % (GeneID, GeneID)
  c.execute(sqlQuery)
  bs = c.fetchall()
  if len(bs) > 0: 
    for row in bs:
      query, subject, blast_score = row
      blastScore = (query, subject, float(blast_score))
      c.execute("SELECT qpham.name, spham.name from pham as qpham, pham as spham where qpham.GeneID = '%s' and spham.GeneID = '%s' and qpham.name = spham.name" % (query, subject))
      if c.rowcount:
        blastScores.append(blastScore)
  return (clustalwScores, blastScores)

def get_scores(c, query, subject):
  '''returns a tuple containing the clustalw and blast scores for the specified genes, using scores_summary'''
  clustalwScore = blastScore = None
  #sqlQuery = "SELECT clustalw_score FROM scores_summary WHERE (query = '%s' AND subject = '%s') OR (query = '%s' AND subject = '%s') ORDER BY clustalw_score DESC" % (query, subject, subject, query)
  sqlQuery = "SELECT clustalw_score FROM scores_summary WHERE query = '%s' AND subject = '%s' AND clustalw_score IS NOT NULL ORDER BY clustalw_score DESC" % (query, subject)
  c.execute(sqlQuery)
  clustalwScore = c.fetchone()
  if clustalwScore:
    clustalwScore = clustalwScore[0]
  else:
    sqlQuery = "SELECT clustalw_score FROM scores_summary WHERE query = '%s' AND subject = '%s' AND clustalw_score IS NOT NULL ORDER BY clustalw_score DESC" % (subject, query) # subject and query ARE REVERSED!
 
    c.execute(sqlQuery)
    clustalwScore = c.fetchone()
    if clustalwScore: clustalwScore = clustalwScore[0]
  sqlQuery = "SELECT MIN(blast_score) FROM scores_summary WHERE ((query = '%s' AND subject = '%s') OR (query = '%s' AND subject = '%s')) AND blast_score IS NOT NULL" % (query, subject, subject, query)
  c.execute(sqlQuery)
  blastScore = c.fetchone()
  if blastScore: blastScore = blastScore[0]
  if clustalwScore: clustalwScore = float(clustalwScore)
  if blastScore: blastScore = float(blastScore)
  return (clustalwScore, blastScore)

# the old, but working, implementation of get_scores()

def get_all_scores(c, query, subject, type='both'):
  '''return a tuple containing the clustalw and blast scores for the query and subject specified'''
  #print 'query:', query, 'subject:', subject
  clustalwScore = blastScore = None
  if type == 'both':
    sqlQuery = "SELECT clustalw.score, blast.score FROM clustalw, blast, alignment AS query, alignment AS subject WHERE query.blast_id = subject.blast_id AND query.blast_id = blast.id AND query.clustalw_id = clustalw.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (query, subject)
  elif type == 'clustalw':
    sqlQuery = "SELECT clustalw.score FROM clustalw, alignment AS query, alignment AS subject WHERE query.clustalw_id = subject.clustalw_id AND query.clustalw_id = clustalw.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (query, subject)
  elif type=='blast':
    sqlQuery = "SELECT blast.score FROM blast, alignment AS query, alignment AS subject WHERE query.blast_id = subject.blast_id AND query.blast_id = blast.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (query, subject)
    #print sqlQuery
  c.execute(sqlQuery)
  row = c.fetchone()
  #print row
  if row:
    if type == 'both':
      clustalwScore, blastScore = row[0], row[1]
      if clustalwScore and blastScore: return (float(clustalwScore), float(blastScore))
    elif type == 'clustalw':
      clustalwScore = row[0]
      if clustalwScore: return float(clustalwScore)
    elif type == 'blast':
      blastScore = row[0]
      if blastScore: return float(blastScore)

  if type == 'both':
    sqlQuery = "SELECT clustalw.score, blast.score FROM clustalw, blast, alignment AS query, alignment AS subject WHERE query.blast_id = subject.blast_id AND query.blast_id = blast.id AND query.clustalw_id = clustalw.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (subject, query)
  elif type == 'clustalw':
    sqlQuery = "SELECT clustalw.score FROM clustalw, alignment AS query, alignment AS subject WHERE query.clustalw_id = subject.clustalw_id AND query.clustalw_id = clustalw.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (subject, query)
  elif type == 'blast':
    sqlQuery = "SELECT blast.score FROM blast, alignment AS query, alignment AS subject WHERE query.blast_id = subject.blast_id AND query.blast_id = blast.id AND query.GeneID = '%s' AND subject.GeneID = '%s' AND query.type = 'Q' AND subject.type = 'S'" % (subject, query)
 
  #print sqlQuery
  c.execute(sqlQuery)
  row = c.fetchone()
  #print row
  if row: clustalwScore, blastScore = row[0], row[1]
  if clustalwScore: clustalwScore = float(clustalwScore)
  if blastScore: blastScore = float(blastScore)
  return (clustalwScore, blastScore)

def get_fasta_from_phage(c, PhageID, type=None, extra=None):
  '''return a string that contains the fasta-formatted data for all genes in a phage genome'''
  data = ''
  if type == 'aa':
    genes = get_genes_from_PhageID(c, PhageID)
    for gene in genes:
      data = '%s>%s_%s\n%s\n' % (data,get_phage_name_from_GeneID(c,gene),get_gene_name_from_GeneID(c,gene),get_translation_from_GeneID(c, gene)) 
      #data = data + '>' + get_phage_name_from_GeneID(c,gene) + get_gene_name_from_GeneID(c,gene) + '\n' + get_seq_from_GeneID(c, gene) + '\n'
      #data = data + '>' + get_gene_name_from_GeneID(c,gene) + '_GeneID(' + gene + ')\n' + get_translation_from_GeneID(c,gene) + '\n'
  elif type == 'nt':
    genes = get_genes_from_PhageID(c, PhageID)
    for gene in genes:
      data = '%s>%s_%s\n%s\n' % (data,get_phage_name_from_GeneID(c,gene),get_gene_name_from_GeneID(c,gene),get_seq_from_GeneID(c, gene, extra)) 
 
  else:
    data = '>%s\n%s\n' % (get_name_from_PhageID(c, PhageID), get_seq_from_PhageID(c, PhageID))
  return data

def get_fasta_from_pham(c, phamName):
  '''return a string that contains the fasta-formatted amino acid data for all genes in a pham'''
  genes = get_members_of_pham(c, phamName)
  data = ''
  for gene in genes:
    data = '%s>%s_%s\n%s\n' % (data,get_phage_name_from_GeneID(c,gene),get_gene_name_from_GeneID(c,gene),get_translation_from_GeneID(c, gene)) 
    #data = data + '>' + get_gene_name_from_GeneID(c,gene) + '_GeneID(' + gene + ')\n' + get_translation_from_GeneID(c,gene) + '\n'
  return data

def get_fasta_nt_from_pham(c, phamName, extra=None):
  '''return a string that contains the fasta-formatted nucleotide data for all genes in a pham'''
  #def get_seq_from_GeneID(c, GeneID, extra=None):
  genes = get_members_of_pham(c, phamName)
  data = ''
  for gene in genes:
    data = '%s>%s_%s\n%s\n' % (data,get_phage_name_from_GeneID(c,gene),get_gene_name_from_GeneID(c,gene),get_seq_from_GeneID(c, gene, extra)) 
    #data = data + '>' + get_phage_name_from_GeneID(c,gene) + get_gene_name_from_GeneID(c,gene) + '\n' + get_seq_from_GeneID(c, gene, extra) + '\n'
    #data = data + '>' + get_gene_name_from_GeneID(c,gene) + '_GeneID(' + gene + ')\n' + get_seq_from_GeneID(c, gene, extra) + '\n'
  return data

def get_phageID_from_pham(c,phamName):
  genes = get_members_of_pham(c, phamName)
  phageIDs = []
  for gene in genes:
    phageID = get_PhageID_from_GeneID(c,gene)
    if phageID not in phageIDs:
      phageIDs.append(phageID)
  return phageIDs

def get_phage_name_from_pham(c, db, phamName):
  if os.path.exists('/tmp/%s/%s/phams/%s/phageNames' % (os.environ['USER'], db, phamName)):
    pkl_file = open('/tmp/%s/%s/phams/%s/phageNames' % (os.environ['USER'], db, phamName), 'rb')
    phageNames = pickle.load(pkl_file)
    pkl_file.close()
  else:
    genes = get_members_of_pham(c, phamName)
    phageNames = []
    for gene in genes:
      phageName = get_phage_name_from_GeneID(c,gene)
      if phageName not in phageNames:
        phageNames.append(phageName)
    output = open('/tmp/%s/%s/phams/%s/phageNames' % (os.environ['USER'], db, phamName), 'wb')
    pickle.dump(phageNames, output)
    output.close() 
  return phageNames
  
def get_phams_from_PhageID(c,phageID):
  allPhams = get_unique_phams(c)
  returnList = []
  for pham in allPhams:
    current = get_phageID_from_pham(c,pham)
    #print "current=" + str(current)
    #print "pham=" + str(pham)
    for cur in current:
      #print "cur=" + cur
      if cur == phageID:
        returnList.append(pham)
  returnList.sort()
  returnList2 = []
  for item in returnList:
    item = str(item)
    returnList2.append(item)   
  return returnList2

def get_unique_phams(c):
  sqlQ = "select distinct name from pham"
  c.execute(sqlQ)
  results = c.fetchall()
  returnList = []
  for r in results:
    returnList.append(r[0])
  return returnList

def reset_blast_table(c):
  print 'The database changed'
  # all BLAST alignments need to be recalculated
  print '..mark BLAST alignments as needing to be redone'
  c.execute("UPDATE gene SET blast_status = 'avail'")
  c.execute("DELETE FROM scores_summary WHERE blast_score IS NOT NULL")
  #c.execute("TRUNCATE TABLE scores_summary")
  #c.execute("DELETE FROM scores_summary WHERE blast_score IS NOT NULL")
  c.execute("COMMIT")
  try:
    phamPub = phamPublisher()
    phamPub.publish_db_update("fasta", 'update available')
    print "done...issue a 'new' message on the 'dataset' channel"
    phamPub.publish("dataset", 'new')
  except:
    pass
    
def phamerator_manage_db_from_genbank_file(c, dirname, filenames):
  for filename in filenames:
    print os.path.join(dirname,filename)
    if os.path.isdir(os.path.join(dirname, filename)):
      print 'ignoring directory %s...' % filename
      continue
    if not filename.endswith('.fixed'):
      continue
    record = parse_GenBank_file(os.path.join(dirname,filename))
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
    try:
      PhageID = add_phage(record, c = c)
    except:
      c.execute("ROLLBACK")
      print "couldn't add phage...exiting"
    if PhageID:
      print "PhageID: %s" % PhageID
      add_genes(record, c = c)
    else: print 'There was an error adding phage', filename, 'to the database.'
    c.execute("COMMIT")

def usage():
  '''Prints program usage information'''
  print """phamerator_manage_db [OPTION] [ARGUMENT]
           -h, --help: print this usage information
           -l, --list: list phages in the database
           -u, --username: database username
           -p, --password: prompt for a database password
           -s, --server: address of the database server
           -d, --database: name of the database on the server
           -i, --import: import a phage into the database from a GenBank file
           -a, --add phage_name: add phage 'phage_name' to the database
           -r, --remove phage_name: remove phage 'phage_name' from the database
               --confirm: True or False - should user be prompted to reset pham assignments?  False means don't reset them
           -c, --create: create a new database
               --clone: used with --create to make the new database a copy of an existing one

           --username, --server, and --database are required, and you must specify
           exactly one of --list, --import, --add, and --remove"""

def main(argv):
  #if 1 not in argv:
  #  usage()
  #  sys.exit()
  addToDbFromNCBI = []
  addToDbFromFile = []
  removeFromDb = []
  listPhages = False
  try:                                
    opts, args = getopt.getopt(argv, "hlpc:u:t:s:d:i:a:r:e:", ["help", "list", "password", "create=", "username=", "server=", "database=", "import=", "add=", 'remove=', "template=", "clone=", 'refseq=', 'confirm='])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  if 'server' not in opts: server = 'localhost'
  if 'username' not in opts: username = None
  if 'password' not in opts: password = None
  if 'confirm' not in opts: confirm = True
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
    elif opt in ("-a", "--add"):
      refseq = False
      for o2, a2 in opts:
        if o2 in ("-e", "--refseq"):
          refseq = a2
      addToDbFromNCBI.append((arg, refseq))
      # add phage
    elif opt in ("-r", "--remove"):
      removeFromDb.append(arg)
    elif opt in ("--confirm",):
      if arg.upper() in ('FALSE', 'NO', 0):
        confirm = False
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
    #cfg = ConfigParser.RawConfigParser()
    #cfg.read(os.path.join(os.environ['HOME'], '.my.cnf'))
    #try:
      #username = cfg.get('client','user')
    #except ConfigParser.NoOptionError:
      username = raw_input('database username: ')
    #try:
      #password = cfg.get('client','password')
    #except ConfigParser.NoOptionError:
      password = getpass.getpass('database password: ')
     
  c = db_conf.db_conf(username=username, password=password, server=server, db=database).get_cursor()
  
  if listPhages:
    phages = get_phages(c, name='name')
    for phage in phages: print phage

  signal.signal(signal.SIGINT, signal_handler)

  original_phages = get_phages(c, PhageID='PhageID')

  for item in addToDbFromFile:
    if os.path.isdir(item):
      response = raw_input('You specified a directory (%s).\nIf you continue, Phamerator will attempt to load all files in this directory and any subdirectories it contains.\nContinue? (y/N) ' % item)
      if response.upper() == 'Y':
        os.path.walk(item, phamerator_manage_db_from_genbank_file, c)
      else:
        print 'input aborted'

    elif os.path.isfile(item):
      if os.path.isabs(item):
        phamerator_manage_db_from_genbank_file(c, os.path.dirname(item), [item])        
      else:
        phamerator_manage_db_from_genbank_file(c, os.path.dirname(os.path.abspath(item)), [item])

  for item in addToDbFromNCBI:
    queryString, refseq = item
    print "searching GenBank for phage '" + queryString + "'"
    NcbiQuery = query.query(queryString, allowRefSeqs=refseq)
    NcbiQuery.run()
    ###
    #feature_parser = GenBank.FeatureParser()
    #ncbi_dict = GenBank.NCBIDictionary('nucleotide', 'genbank', parser = feature_parser)
    from Bio import Entrez, SeqIO
    handle = Entrez.efetch(db='nucleotide', id=queryString, rettype='gb', retmode='text')
    results = SeqIO.read(handle, 'gb')
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
      problems = check_record_for_problems(result)
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

      PhageID = add_phage(result,c=c)
      if PhageID:
        add_genes(result, c = c)
        # don't need to add rows to alignment, clustalw or blast anymore
        #add_alignments(PhageID, c = c)
      else: print 'There was an error adding phage', item, 'to the database.'
      c.execute("COMMIT")
  for item in removeFromDb:
    print arg
    try:
      type, id = arg.split(':')
      print 'type is %s' % type
    except:
      print 'arg is %s' % arg
      print "please specify the phage preceded with 'Name:' or 'PhageID:'"
      sys.exit()
    if type.upper() == 'NAME': PhageID = get_PhageID_from_name(c, id)
    elif type.upper() == 'PHAGEID':
      pass
    else:
      print type
      print "please specify the phage preceded with 'Name:' or 'PhageID:'"
      sys.exit()
    print "removing phage '" + id + "' from the database"
    remove_phage_from_db(id, c, confirm)
  new_phages = get_phages(c, PhageID='PhageID')
  #reset_blast_table(c)
  if phages_have_changed(original_phages, new_phages):
    print 'Deleting BLAST and ClustalW scores means that the database will need to be recomputed. If you choose to NOT delete these scores, only undone alignments will be computed the next time you run ClustalW or BLAST.'
    go = raw_input("Do you want to delete all BLAST and ClustalW scores [y/N]: ").upper()
    if go == 'Y': reset_blast_table(c)
    else:
      print 'BLAST and ClustalW scores were not deleted.'
      return
  
  #  phamPub.publish_db_update("fasta", 'BLAST database is current') if __name__ == '__main__': main(sys.argv[1:])

if __name__ == '__main__':
  main(sys.argv[1:])
