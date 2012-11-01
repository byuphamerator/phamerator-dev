#!/usr/bin/env python

try:
  from phamerator import *
  from phamerator.phamerator_manage_db import *
  from phamerator.db_conf import db_conf
  import sys
except:
  import sys, os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
  sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
  from phamerator import *
  from phamerator.phamerator_manage_db import *
  from phamerator.db_conf import db_conf

def get_finals(c):
  c.execute("SELECT name FROM phage WHERE status = 'final'")
  rows = c.fetchall()
  finals = []
  for row in rows:
    finals.append(row[0])
  return finals

def get_drafts(c):
  c.execute("SELECT name, phageid FROM phage WHERE status = 'draft'")
  rows = c.fetchall()
  drafts_raw = []
  for row in rows:
    drafts_raw.append(row)
  drafts = []
  for row in drafts_raw:
    name = row[0]
    if name.find('-') != -1:
      drafts.append((name.split('-')[0], row[1]))
    elif name.find('_') != -1:
      drafts.append((name.split('_')[0], row[1]))
    else:
      drafts.append((name, row[1]))
  return drafts

def remove_drafts(c, drafts, finals):
  for draft in drafts:
    name, phageid = draft
    print draft
    remove_phage_from_db(phageid, c, confirm=False)

def main():
  cfg = ConfigParser.RawConfigParser()
  cfg.read(os.path.join(os.environ['HOME'], '.my.cnf'))
  import sys
  db = sys.argv[1]
  try:
    username = cfg.get('client','user')
  except ConfigParser.NoOptionError:
    username = raw_input('database username: ')
  try:
    password = cfg.get('client','password')
  except ConfigParser.NoOptionError:
    import getpass
    password = getpass.getpass('database password: ')

  c = db_conf(username='root', password=password, server='localhost', db=db).get_cursor()
  finals = get_finals(c)
  print 'finals:', finals
  drafts = get_drafts(c)
  print 'drafts:', drafts

  print 'removing the following phages:\n'
  remove_drafts(c, drafts, finals)

if __name__ == '__main__':
  main()
