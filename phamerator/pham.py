#!/usr/bin/env python

import time, sys, random, colorsys, string, db_conf, logger
from phamerator_manage_db import *
#from db import *

class DuplicatePhamError(Exception):
  def __init__(self,value):
    self.parameter=value
  def __str__(self):
    print 'Duplicate Pham Error!'
    return repr(self.parameter)

class errorHandler:
  def __init__(self):
    self._logger = logger.logger(True)
  def show_sql_errors(self, c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      self._logger.log(error)
    print 'exiting on database error  :('
    sys.exit()

class db(errorHandler):
  '''class to handle database operations'''
  def __init__(self, c):
    errorHandler.__init__(self)
    self.c = c
  def insert(self, table, *args, **kargs):
    '''insert values into the specified table'''
    columns = []
    values = []
    for key in kargs.keys():
      columns.append(str(key))
      values.append(str(kargs[key]))
    sqlQuery = "INSERT INTO " + table + " (" + string.join(columns, ", ") + " ) VALUES ('" + string.join(values, "','") + "')"  
    try:
      self.c.execute(sqlQuery)
      #print sqlQuery
    except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      print 'SQL query error!'
      print sqlQuery
      self.show_sql_errors(self.c)

  def select(self, table, *args, **kargs):
    '''execute a select statement based on provided data and return the result'''
    if 'func' in kargs.keys():
      sqlQuery = "SELECT %s(%s) FROM %s" % (kargs['func'], kargs['parameter'], table)
      #print sqlQuery
      try: self.c.execute(sqlQuery)
      except:
        print sqlQuery
        self.show_sql_errors(self.c)
      return self.c.fetchone()[0]
    else:
      #print 'args:', args
      #print 'len(args):', len(args)
      #print 'kargs:', kargs
      if len(args) == 1: selection = args[0]
      else: selection = string.join(args, ",")
      condition = ''
      for key in kargs.keys():
        if condition: condition += ' AND '
        if key == 'join':
          clauses = kargs[key].split(' ')
          #print 'clauses:', clauses
          for n, clause in enumerate(clauses):
            #print 'clause:', clause
            j1, j2 = clause.split(':')
            if n > 0: condition += ' AND '
            condition += str(j1) + " = " + str(j2)
        else:
          condition = condition + str(key) + " = '" + str(kargs[key]) + "'"
      if condition:
        sqlQuery = "SELECT %s FROM %s WHERE %s" % (selection, table, condition)
      else:
        sqlQuery = "SELECT %s FROM %s" % (selection, table)
      #print 'sqlQuery:', sqlQuery
      try: self.c.execute(sqlQuery)
      except:
        print 'SQL ERROR!!!'
        print sqlQuery
        self.show_sql_errors(self.c)
      return self.c.fetchall()

  def delete(self, table, *args, **kargs):
    '''execute a delete statement based on provided data and return the result'''
    columns = []
    values = []
    condition = ''
    for key in kargs.keys():
      if condition: condition += ' AND '
      condition = condition + str(key) + " = '" + str(kargs[key]) + "'"
    sqlQuery = "DELETE FROM %s WHERE %s" % (table, condition)
    try: self.c.execute(sqlQuery)
    except:
      print sqlQuery
      self.show_sql_errors(self.c)

  def commit(self):
    '''commit the transaction to the database'''
    self.c.execute("COMMIT")

class Pham(errorHandler):
  '''Basic class for holding information about the members of a pham'''
  def __init__(self, name=None, members=[], children=[]):
    self.name = name
    self.members = members
    self.children = children
    #self.name = ''
    #self.members = []
    #self.children = []

  def __repr__(self):
    m = string.join(self.members, ', ')
    if self.children:
      c = ''
      for i in self.children: c = c + str(i)
      return "pham %s\n  members: %s\n  children: %s" % (self.name, m, c)
    else:
      return "pham %s\n  members: %s\n" % (self.name, m)

  def __lt__(self, other):
    # if all the genes in the left pham are in the right pham and the phams are not equal, return True
    self.members.sort()
    other.members.sort()
    if self == other: return False
    for gene in self.members:
      if gene not in other.members:
        return False
    return True

  def __eq__(self, other):
    '''return true if the two phams have exactly the same members, and otherwise return false'''
    self.members.sort()
    other.members.sort()
    if self.members == other.members: return True
    else: return False

  def add_members(self, members):
    '''add member(s) to a pham, if they are not already in the pham'''
    for member in members:
      if member not in self.members:
        #print 'adding', member, 'to pham', self.name
        self.members.append(member)

  def has_member(self, GeneID):
    '''returns true if this pham contains the specified gene, otherwise returns false'''
    if GeneID in self.members: return True
    else: return False

class PhamController(errorHandler):
  '''Class for holding groups of Pham objects''' 
  def __init__(self, c, source=None):
    '''initialize instance specific variables, and (if requested), load phams from db'''
    self.c = c
    self.phams = []
    self.phamListMax = 0
    self.db = db(c)
    self.next_avail_pham_name = None
    if source == 'db':
      phams = get_phams(self.c)
      dict = {}
      keys = dict.keys()
      for name, GeneID in phams:
        name = int(name)
        if dict.has_key(name): dict[name].append(GeneID)
        else:  dict[name] = [GeneID]
        keys = dict.keys()
        keys.sort()
      for name in keys:
        #try:
        p = Pham(name=name, members=dict[name], children=[])
        self.add_pham(p)
        #except DuplicatePhamError:
        #  pass
        #p.members.append(GeneID)

  def find_phams_with_gene(self, GeneID):
    '''returns true if the specified GeneID is in an pham in this controller.  Otherwise returns false'''
    r = []
    for p in self.get_pham():
      if p.has_member(GeneID): r.append(p)
    return r
        
  def add_pham(self, pham):
    '''add a pham to the controller list if there is no other pham with the same name'''
    if len(self.phams) < 1:
      self.phams.append(pham)
      return
    for p in self.phams:
      # if the current pham has a name that is not unique
      if pham.name and p.name == pham.name:
        raise DuplicatePhamError('a pham named ' + str(p.name) + ' is already in this phamController instance')
        break

      # if the current pham has exactly the same members as a previously existing pham
      elif p == pham:
        #print p.members, pham.members
        #for x in self.phams: print x.members
        raise DuplicatePhamError('pham ' + str(p) + 'with name' + str(p.name) + ' with members ' + string.join(p.members, ',') + ' in this phamController instance has the exact same members as pham: ' + str(pham) + 'with name' + str(pham.name) + string.join(pham.members, ','))
        break

      # if the current pham's member list is a superset of a previous pham's member list
      elif p < pham:
        #print "members of p are a subset of the members of pham"
        # if there are >= 2 children of pham, then pham is a super-pham and the children should be marked as such in pham_history
        # else, p has just grown some, so add the new members to p
        p.add_members(pham.members)
        break

    #print 'appending pham'
    #pham.name = # key next avail key
    self.phams.append(pham)
    
  def check_old_phams(self):
    print 'checking existing phams to see if they are still valid before modifying the database...'
    for o in oldController.get_pham():
      current_relatives = []
      for GeneID in o.members:
        relatives = get_all_relatives(GeneID)
        for relative in relatives:
          if relative not in current_relatives: current_relatives.append(relative)
      for GeneID in o.members:
        if GeneID not in current_relatives:
          "pham 'o' should be split into multiple child phams"

  def __sub__(self, oldController):
    print 'there are', len(oldController.phams), 'phams already in the database and', len(self.phams), 'total phams'
    delete = []   # list of phams in self.phams that should be deleted because they're already in the db
    for o in oldController.get_pham():
      for n in self.get_pham():
        if o == n:
          #print 'deleting %s because it equals %s' % (n, o)
          delete.append(n)
        # before doing the following, I need to check to see if pham o is still valid
        #elif n < o:
        #  print 'deleting %s because it is < %s' % (n, o)
        #  delete.append(n)
        #if o <= n: delete.append(n)
    delete.sort()
    delete.reverse()
    #print 'deleting %s phams from newController because they are already in the database' % len(delete)
    for d in delete: 
      print 'pham %s is already in the database, so removing it from the newController' % (d)
      print len(self.get_pham())
      self.remove_pham(d)
      print len(self.get_pham())
    newPhams = self.get_pham()
    for o in oldController.get_pham():
      #print o
      for n in newPhams:
        #print n, 'n.children:', n.children
        if not n.name:
          #print '-'*80, n, '-'*80
          n.name = self.get_next_avail_pham_name()
          #print 'unnamed pham needs a name.  using:', n.name
        if n < o:
          # The old pham has been split up, probably because adding phage(s) has slightly worsened all BLAST e-values 
          # This is correct behavior, although a rare situation
          # leave the new phams alone, but move the old one to pham_old and mark it in pham_history
          #print 'fixing an old pham that has been split into 2 or more new phams...'
          print 'old pham %s is being split up.  %s is a child pham' % (o.name, n.name)
          print '*' * 80
          print 'o.name: %s' % o
          print 'o.children: %s' % o.children
          print 'n.name: %s' % n
          # mark the old pham as being the parent of the new (subset) pham
          print 'INSERTING INTO pham_history.  name: %s :: parent: %s :: split' % (n.name, o.name)
          self.db.insert(table='pham_history', name=n.name, parent=o.name, action='split')
          # for each gene in the old (superset) pham
          for GeneID in o.members:
            # if its in the new pham, do nothing
            # otherwise...
            if GeneID not in n.members:
              # put the gene in pham_old, unless it's already there with the old pham name
              if not self.db.select('pham_old', 'name', name=o.name, GeneID=GeneID):
                self.db.insert(table='pham_old', name=o.name, GeneID=GeneID)
            # delete the old gene from pham
            self.db.delete(table='pham', name=o.name, GeneID=GeneID)
          self.db.commit()
          #print 'fixed!'
        if o < n:
          #print o.name, 'is a child of', n.name
          #print 'these genes', o.members, 'should all be in', n.members
          n.children.append(int(o.name))    # mark o as a child of n
        #else: print o.name, 'is NOT a child of', n.name
    #for m in newPhams: print 'm.name:', m.name, 'm.members:', m.members, 'm.children:', m.children
    delete = []
    print 'number of new phams:', len(self.phams)
    print '*' * 80
    #print 'New phams'

    for m in newPhams:
      #print m.name, m.members, 'm.children', m.children
      if len(m.children) == 1:    # pham o has grown, so add the new members
        #print 'm:', m, 'm.name:', m.name, 'm.children:', m.children
        o = oldController.get_pham(name=int(m.children[0]))[0]  # get the pham whose name is that of m's child
        #print o.name, 'is growing'
        #print o.name, ':', o.members, 'should all be in', m.name, ':', m.members
        members = m.members
        #print 'removing', m.name, m.members, 'because members have been added to', o.name, o.members
        #self.remove_pham(m)
        #delete.append(m)
        #o.add_members(members)
        m.name = int(o.name)
        #print 'now this should contain all the members above', o.members
        #if not self.has_pham(o):
        #  print 'this %s, %s is not in the newController, so adding it' % (o.name, o.members)
        #  self.add_pham(o)
        #else:
        #  print 'this %s, %s is already in the newController, so not adding it' % (o.name, o.members)

      elif len(m.children) >= 2:  # pham n has joined >=2 old phams together
        print '%s is a super-pham with children %s' % (m.name, m.children)
        #child: child pham name
        #n.name: parent pham name
        for child in m.children:
          try: p = oldController.get_pham(name=child)[0]
          except: continue
          #member: child GeneID
          #print 'adding %s -> %s to pham_history' % (child, m.name)
          print self.db.select('pham_history', 'name', 'parent', name=child)
          self.db.insert(table='pham_history', name=child, parent=m.name, action='join')
          for member in p.members:
            #print 'adding %s -> %s to pham_old' % (child, member)
            self.db.insert(table='pham_old', name=child, GeneID=member)
            #print 'deleting %s -> %s from pham' % (child, member)
            self.db.delete(table='pham', name=child, GeneID=member)
            self.db.commit()
    #for c in self.phams: print c.members
    delete.sort()
    delete.reverse()
    print 'deleting', len(delete), 'phams'
    for d in delete:
      #print 'removing pham %s, %s because its members are already in another pham' % (d.name, d.members)
      self.remove_pham(name=d.name)
    print len(self.phams), 'phams will be added to the database'
    return self

  def has_pham(self, pham):
    '''return true if the given pham is present, otherwise return false'''
    pham.members.sort()
    for p in self.phams:
      p.members.sort()
      if p.members == pham.members: return True
    return False

  def get_pham(self, name=None, member=None):
    '''retrieve a pham by name or by a the presence of a particular member'''
    if name and not member:
      for p in self.phams:
        if int(p.name) == int(name):
          return [p]
      # if there are no matches, return None
      return None
    elif name and member:
      for p in self.phams:
        if p.name == name and member in p.members:
          return [p]
      # if there are no matches, return None
      return None
    elif member and not name:
      matches = []
      for p in self.phams:
        if member in p.members:
          matches.append(p)
      # if there are matches, return them in a list
      if len(matches) >= 1: return matches
      # if there are no matches, return None
      else: return None
    # if caller didn't specify search criteria, return all phams
    else:
      return self.phams

  def remove_pham(self, pham=None, name=None):
    '''remove a pham from the controller list'''
    # print self, pham, name
    #for j in self.phams: print j.name
    if name:
      result = None
      #print 'trying to delete by name =', name
      #print 'there are', len(self.phams), 'to check'
      for p in range (0, len(self.phams)):
        #print self.phams[p].name
        if int(self.phams[p].name) == int(name):
          result = self.phams.pop(p)
        #else: print int(self.phams[p].name), '!=', int(name)
      if result: print 'deleted 1 pham by name =', result.name
    elif pham:
      #print 'trying to delete by pham'
      tempPhams = self.phams
      #print 'there are', len(tempPhams), 'phams'
      delete = []
      for index in range(0, len(tempPhams)):
        if tempPhams[index] == pham:
          #print 'deleting pham', tempPhams[index].name, tempPhams[index].members
          delete.append(index)
      delete.sort()
      delete.reverse()
      for d in delete:
        self.phams.pop(d)
      #del pham

  def join_phams(self, phams):
    '''join two or more phams together, and return the resulting pham'''
    print 'joining phams:', phams
    p = Pham(name=None, members=[], children=[])
    p.members.sort()
    num = len(self.phams)
    for q in phams:
      q.members.sort()
      p.add_members(q.members)
      #print 'deleting pham %s' % q
      self.remove_pham(pham=q)
    #print 'deleted', num - len(self.phams), 'phams'
    return p

  def get_next_avail_pham_name(self):
    '''return the next available number that can be used as a valid pham name'''

    if not self.next_avail_pham_name:
      self.next_avail_pham_name = 0
    
    i = self.next_avail_pham_name + 1
    while 1:
      self.c.execute("select * from pham where name = '%s'" % i)
      a = self.c.rowcount
      self.c.execute("select * from pham_old where name = '%s'" % i)
      b = self.c.rowcount
      self.c.execute("select * from pham_history where name = '%s'" % i)
      c = self.c.rowcount
      self.c.execute("select * from pham_history where parent = '%s'" % i)
      d = self.c.rowcount

      if a == 0 and b == 0 and c == 0 and d == 0: #and i not in self.allocatedPhamNames:
        self.next_avail_pham_name = i
        return i
      i = i + 1

  def save(self):
    '''save phams to the database'''
    print 'saving phams....'
    print 'phams: %s' % self.phams
    for p in self.phams:
      # if the pham already has a name, use it
      if not p.name: p.name = self.get_next_avail_pham_name()
      print 'saving pham', p.name
      for member in p.members:
        #self.db.select('pham', name=p.name, GeneID=member)
        if self.db.select('pham', 'name', 'GeneID', name=p.name, GeneID=member) == ():
          #print "inserting '%s' into pham '%s'" % (member, p.name)
          self.db.insert(table='pham', name=p.name, GeneID=member)
          self.db.commit()
        #print self.db.select('pham_color', 'name', name=p.name)
      if self.db.select('pham_color', 'name', name=p.name) == ():
        print 'assigning color'
        pV = PhamView(self.c)
        pV.assign_color(p.name)
      else:
        #print 'NOT assigning color'
        pass
    self.db.commit()

class PhamView(Pham):
  def __init__(self, c):
    self.c = c
  def assign_color(self, name):
    '''create a random color and return it'''
    h=s=v=0
    while h <= 0: h = random.random()
    while s < 0.5: s = random.random()
    while v < 0.8: v = random.random()
    rgb = colorsys.hsv_to_rgb(h,s,v)
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    hexrgb = '#%02x%02x%02x' % rgb
    try:
      print "in assign_color"
      #print "INSERT INTO pham_color(name, color) VALUES (%s, '%s')" % (name, hexrgb)
      self.c.execute("INSERT INTO pham_color(name, color) VALUES (%s, '%s')" % (name, hexrgb))
      self.c.execute("COMMIT")
    except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
 
      print "error in 'assign_color'"
      self.show_sql_errors(self.c)
      sys.exit()
    try: self.c.execute("COMMIT")
    except MySQLdb.Error, e:
      print 'cannot commit pham_color'
      self.show_sql_errors(self.c)
