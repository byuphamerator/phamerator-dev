#!/usr/bin/env python

import db_conf
import getpass
from phamerator_manage_db import *
password = getpass.getpass()
c = db_conf.db_conf(username='steve', password=password, server='djs-bio.bio.pitt.edu', db='Hatfull').get_cursor()
phages = get_phages(c, name=True)
for p in phages:
  print p, str(get_percent_GC(c, name=p))+'%', get_genome_length(c,name=p), get_number_of_genes(c, name=p)
