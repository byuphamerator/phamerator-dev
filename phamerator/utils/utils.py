import sys, os, shutil, ConfigParser
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ConfigChecker:
  def __init__(self, file=None):
    if not file:
      file = os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf')
    print 'checking %s' % file
    self.check_formatting(file)
    self.check_data(file)
    
  def check_formatting(self, file):
    '''expand ~'s and remove "'s from the config file'''
    try:
      i = open(file)
      lines = i.readlines()
      i.close()
      
      outlines = []
      for line in lines:
        l = line.replace('~', os.environ['HOME'])
        l = l.replace('"', '')
        outlines.append(l)
      #print outlines
      o = open(file, 'w')
      for line in outlines:
        o.write(line)
      o.close()
    except:
      self.replace_config_file(file)

  def replace_config_file(self, file):
    if not os.path.exists(os.path.dirname(file)):
      print '~/.phamerator directory is missing--creating one for you'
      os.mkdir(os.path.dirname(file))
    elif not os.path.exists(file):
      print 'phamerator.conf file is missing--creating one for you'
      try: 
        shutil.copyfile(os.path.join(os.curdir, 'config', 'phamerator.conf.sample'), file)
      except:
        shutil.copyfile(os.path.join('/usr/share/phamerator/config/', 'phamerator.conf.sample'), file)
    else:
      print 'phamerator.conf exists but is not valid.  Resetting to default values'
      from dialogs.dialogs import InvalidConfigurationDialog
      invalidConfigurationDialog = InvalidConfigurationDialog()
      invalidConfigurationDialog.run()
      try:
        shutil.copyfile(os.path.join(os.curdir, 'config', 'phamerator.conf.sample'), file)
      except:
        shutil.copyfile(os.path.join('/usr/share/phamerator/config/', 'phamerator.conf.sample'), file)

  def check_data(self, file):
    '''make sure that the file has the appropriate sections'''
    #try:
    cfg = ConfigParser.RawConfigParser()
    cfg.read(file)
    try:
      defaultServer = cfg.get('Phamerator','defaultServer')
      otherServers = cfg.get('Phamerator','otherServers')
    except:
      self.replace_config_file(file)
      return

    otherServers = otherServers.split(',')
    
    if not defaultServer and not otherServers:
      print 'no servers configured'
      return
    elif otherServers and not defaultServer:
      defaultServer = otherServers.pop(0)
      
    # if no servers are configured, make otherServers an empty list, not a list with an empty string
    if otherServers == ['']:
      otherServers = []
    if defaultServer in otherServers:
      otherServers.remove(defaultServer)
    import string
    cfg.set('Phamerator','defaultServer', defaultServer)
    cfg.set('Phamerator','otherServers', string.join(otherServers, ','))
    
    cfg_file = open(file, 'w')
    cfg.write(cfg_file)
    cfg_file.close()
