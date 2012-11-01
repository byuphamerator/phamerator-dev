#!/usr/bin/python

import gconf, os

class PhameratorConfiguration:
  def __init__(self):
    # add keys if needed
    self.client = gconf.client_get_default()
    self.gconf_dir = '/apps/phamerator'
    if not self.client.dir_exists(self.gconf_dir):
      self.client.add_dir(self.gconf_dir, gconf.CLIENT_PRELOAD_NONE)

    entries = self.client.all_entries(self.gconf_dir)
    self.gconf_strings = [
                         '/apps/phamerator/gene_color',
                         '/apps/phamerator/default_save_folder',
                         '/apps/phamerator/pham_circle_color_scheme'
                         ]

    self.gconf_bools = [
                       '/apps/phamerator/show_pham_names',
                       '/apps/phamerator/show_alignment_text',
                       '/apps/phamerator/show_alignment',
                       '/apps/phamerator/show_domains'
                       ]
    self.gconf_ints = []
    self.gconf_floats = ['/apps/phamerator/transparency_adjustment']

    entries = self.client.all_entries('/apps/phamerator')
    #for entry in entries: print entry.get_key()

    # for each bool, check if it's in the gconf database
    # and add it if needed
    keys = []
    for entry in entries:
      keys.append(entry.get_key())
    for bool in self.gconf_bools:
      if bool not in keys:
        self.client.set_bool(bool, True)
        print "can't find %s in %s" % (bool, self.gconf_bools)

    # for each float, check if it's in the gconf database
    # and add a defualt value if needed
    keys = []
    for entry in entries:
      keys.append(entry.get_key())
    for flt in self.gconf_floats:
      if flt not in keys:
        if flt == '/apps/phamerator/transparency_adjustment':
          self.client.set_float(flt, 1.0)


    # for each string, check if it's in the gconf database
    # and, if not, add a reasonable default value
    keys = []
    for entry in entries:
      keys.append(entry.get_key())
    for s in self.gconf_strings:
      try:
        if s not in keys:
          if s == '/apps/phamerator/gene_color':
            self.client.set_string('/apps/phamerator/gene_color', 'pham')
          elif s == '/apps/phamerator/default_save_folder':
            self.client.set_string('/apps/phamerator/default_save_folder', os.environ['HOME'])
          elif s == '/apps/phamerator/pham_circle_color_scheme':
            self.client.set_string('/apps/phamerator/pham_circle_color_scheme', 'alignmentType')
      except:
        pass

  def set_bool(self, key, param):
    print 'setting bool %s:%s' % (key, param)
    self.client.set_bool(key, param)

  def get_bool(self, key):
    print 'getting bool %s' % (key)
    return self.client.get_bool(key)

  def set_float(self, key, param):
    print 'setting float %s:%s' % (key, param)
    self.client.set_float(key, param)

  def get_float(self, key):
    print 'getting float %s' % (key)
    return self.client.get_float(key)

  def set(self, key, param):
    print 'setting string %s:%s' % (key, param)
    self.client.set_string(key, param)
 
  def get(self, key):
    print 'getting string %s' % (key)
    return self.client.get_string(key)
