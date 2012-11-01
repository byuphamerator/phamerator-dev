#!/usr/bin/env python

import MySQLdb
import getpass

class AuthenticationError(Exception):
  def __init__(self, username, password, server, db, msg):
    self.username, self.password, self.server, self.db, self.msg = username, password, server, db, msg
    print 'AuthenticationError: username %s, server %s, db %s, msg %s' % (self.username, self.server, self.db, self.msg)
  def __repr__(self):
    print 'AuthenticationError: username %s, server %s, db %s' % (self.username, self.server, self.db)
  #  #return 'AuthenticationError: username %s, server %s, db %s, message %s' % (self.username, self.server, self.db, self.message)

class db_conf:
  def __init__(self, username = None, password = None, server='127.0.0.1', db=None):
    try:
      self.conn = MySQLdb.connect(host=server, user=username, passwd=password, db=db)
      self.c = self.conn.cursor()
      self.error = None
    except MySQLdb.OperationalError, message:
      self.error = message
      print 'Error message:', message
      raise AuthenticationError(username, password, server, db, message)

  def get_conn(self):
    return self.conn
  def get_cursor(self):
    return self.c 
