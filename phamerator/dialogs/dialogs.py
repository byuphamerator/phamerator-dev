import sys, os, string, threading, gconf
import pygtk, gtk
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ui.ui import gladeFile
from utils.utils import *
from phamerator_manage_db import *
import logger
import config
import ConfigParser
import urllib2
import cairo
import gconf

class Phage:
  def __init__(self):
    self.name = ''

class Phage:
  def __init__(self):
    self.name = ''

class Dialog:
  """Generic dialog class"""
  def __init__(self, name=None):
    #setup the glade file
    self.gladefile = gladeFile().filename
    self.client = gconf.client_get_default()
    self.conf = config.PhameratorConfiguration()
    self.current_folder = self.conf.get('/apps/phamerator/default_folder')
    if not self.current_folder: self.current_folder = os.path.join(os.environ['HOME'], 'Desktop')
    #self.wTree = gtk.glade.XML(self.gladefile, name)
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, [name])
    if name is not None: self.wTree.get_object(name).set_current_folder(self.current_folder)
  def set_current_folder(self, folder):
    self.conf.set('/apps/phamerator/default_folder', folder)

class PreferencesDialog:
  def __init__(self,pManager):
    self.PManager = pManager
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "preferencesDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["preferencesDialog"])
    dic = {"preferencesChangedSignalHandler" : self.preferencesChangedSignalHandler,
           "radioChangedSignalHandler":self.radioChangedSignalHandler,
           "on_preferencesServerComboBox_changed": self.on_preferencesServerComboBox_changed,
           "on_preferencesDatabaseComboBox_changed": self.on_preferencesDatabaseComboBox_changed,
           "on_updateDatabaseButton_clicked": self.on_updateDatabaseButton_clicked,
           "on_addServerButton_clicked": self.on_addServerButton_clicked,
           "on_removeServerButton_clicked": self.on_removeServerButton_clicked,
           "on_addDatabaseButton_clicked": self.on_addDatabaseButton_clicked,
           "on_removeDatabaseButton_clicked": self.on_removeDatabaseButton_clicked,
           }
    self.dlg = self.wTree.get_object("preferencesDialog")
    spinner = self.wTree.get_object("preferencesDialogSpinner")
    spinner.start()
    conf = config.PhameratorConfiguration()
    if conf.get('/apps/phamerator/pham_circle_color_scheme') == 'alignmentType':
      self.wTree.get_object("alignmentTypeRadioButton").set_active(True)
      self.wTree.get_object("phamColorRadioButton").set_active(False)
    if conf.get('/apps/phamerator/pham_circle_color_scheme') == 'phamColor':
      self.wTree.get_object("alignmentTypeRadioButton").set_active(False)
      self.wTree.get_object("phamColorRadioButton").set_active(True)
    adj = self.wTree.get_object("transparency_slider").get_adjustment()
    adj.configure(conf.get_float('/apps/phamerator/transparency_adjustment'), 0.0, 100.0, 1.0, 10.0, 0)
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    if cfg.get('Phamerator','draw_blast_alignments') == 'False':
      self.wTree.get_object("eValuesCheckBox").set_sensitive(False)
      self.wTree.get_object("blastAlignmentCheckBox").set_sensitive(False)
    #self.wTree.signal_autoconnect(dic)
    self.wTree.connect_signals(dic)
    try:
      self.database = cfg.get('Phamerator','defaultDatabase')
      print "self.database = " + self.database
    except: self.database = 'SEA'
    try: self.remote_server = cfg.get('Phamerator','defaultServer')
    except:
      pass
      self.remote_server = 'http://localhost'


    comboBoxes = [('server', 'preferencesServerComboBox'), ('database', 'preferencesDatabaseComboBox')]
    for box in comboBoxes:
      boxType, boxName = box[0], box[1]
      cbe = self.wTree.get_object(boxName)
      listStore = gtk.ListStore(str)
      cbe.set_model(listStore)
      
      cell = gtk.CellRendererText()
      cbe.pack_start(cell, True)
      cbe.add_attribute(cell, "text", 0)
      
      #cbe.set_text_column(0)
      if boxType == 'server':
        others = cfg.get('Phamerator','otherServers')
      elif boxType == 'database':
        others = cfg.get('Phamerator','otherDatabases')
      otherList = others.split(',')
      otherListNew = []
      for n,o in enumerate(otherList):
        if o != "":
          otherListNew.append(o.strip())
      otherListNew.sort()
      for o in otherListNew:
        print o
        listStore.append(row=(o,))
      if boxType == 'server' and self.remote_server:
        print 'POPULATING SERVER COMBOX BOX with %s' % self.remote_server
        #listStore.prepend(row=(self.remote_server,))
        cbe.prepend_text(self.remote_server)
      elif boxType == 'database':
        cbe.prepend_text(self.database)
      cbe.set_active(0)

  def radioChangedSignalHandler(self,widget):
    conf = config.PhameratorConfiguration()
    if self.wTree.get_object("alignmentTypeRadioButton").get_active()==True:
      conf.set('/apps/phamerator/pham_circle_color_scheme','alignmentType')
    elif self.wTree.get_object("phamColorRadioButton").get_active()==True:
      conf.set('/apps/phamerator/pham_circle_color_scheme','phamColor')
    if self.PManager.wTree.get_object("phamCircleToggleToolButton").get_active() == True:
      self.PManager.draw_phamCircle_canvas()
      self.PManager.phamCircleWTree.get_object('phamCircleWindow').show()

  def preferencesChangedSignalHandler(self,widget):
    conf = config.PhameratorConfiguration()
    print str(self.wTree.get_object("transparency_slider").get_adjustment().get_value())
    conf.set_float('/apps/phamerator/transparency_adjustment',self.wTree.get_object("transparency_slider").get_adjustment().get_value())
    if self.PManager.wTree.get_object("phamCircleToggleToolButton").get_active() == True:
      self.PManager.phamCircle.set_threshold(self.wTree.get_object("transparency_slider").get_adjustment().get_value()/100)
      self.PManager.phamCircle.update_arc_groupModel(self.PManager.phamCircleWTree.get_object("arc_scale").get_adjustment().get_value()/100)

  def on_preferencesServerComboBox_changed(self, widget):
    print 'on_preferencesServerComboBox_changed!!!'
    spinner = self.wTree.get_object('preferencesDialogSpinner')
    spinner.start()
    label = self.wTree.get_object('preferencesStatusLabel')
    label.set_text('checking settings...')
    ConfigChecker()
    newServer = widget.get_active_text()
    print 'newServer is %s' % newServer
    if newServer and not newServer.startswith('http://'):
      newServer = 'http://%s' % newServer
      
    if not newServer:
      newServer = ''
      
    newDatabase = self.wTree.get_object('preferencesDatabaseComboBox').get_active_text()
    
    model = widget.get_model()
    otherServers = set()
    iter = model.get_iter_first()
    while iter:
      print 'adding',model.get_value(iter,0)
      otherServers.add(model.get_value(iter,0))
      iter = model.iter_next(iter)
    
    try:  otherServers.remove(newServer)
    except KeyError: pass
    otherServers = list(otherServers)
    otherServers = string.join(otherServers, ',')
    print otherServers
    
    import ConfigParser
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))

    self.server = cfg.get('Phamerator','defaultServer')
    if not self.server.startswith('http://'):
      self.server = 'http://%s' % self.server

    print "checking server: %s" % (newServer)
    valid = False
      
    sharedDatabase = Shared()
    sharedServer = Shared()
    serverCheckerEvnt = threading.Event()
    serverCheckerEvnt.clear()
    timeout = 10

    serverChecker = ServerDatabaseChecker(sharedServer, serverCheckerEvnt, newServer, timeout)
    serverChecker.start()
    
    while not serverCheckerEvnt.isSet():
      serverCheckerEvnt.wait(0.1)
      while gtk.events_pending():
        gtk.main_iteration(False)

    databaseCheckerEvnt = threading.Event()
    databaseCheckerEvnt.clear()
    
    databaseChecker = ServerDatabaseChecker(sharedDatabase, databaseCheckerEvnt, '%s/%s.sql' % (newServer, newDatabase), timeout)
    databaseChecker.start()
    
    while not databaseCheckerEvnt.isSet():
      databaseCheckerEvnt.wait(0.1)
      while gtk.events_pending():
        gtk.main_iteration(False)

    if sharedServer.status and sharedDatabase.status:
      print newServer + " is a valid server, adding to phamerator.conf"
      label.set_text('')
      valid = True

    elif sharedServer.status and not sharedDatabase.status:
      print newServer + " is a valid server, adding to phamerator.conf"
      label.set_text("database '%s' is not available on this server" % newDatabase)
      valid = True

    else:
      valid = False
      if newServer:
        label.set_text('cannot connect to server %s' % newServer)
      else:
        label.set_text('please add a server')
      print 'WARNING!  Cannot connect to server %s' % newServer

    cfg.set('Phamerator','otherServers', otherServers)
    cfg.set('Phamerator','defaultServer', newServer)
    #if valid:
    cfg_file = open(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'), 'w')
    cfg.write(cfg_file)
    cfg_file.close()
    spinner.stop()
    return
 
  def on_preferencesDatabaseComboBox_changed(self, widget):
    print 'on_preferencesDatabaseComboBox_changed!!!'
    spinner = self.wTree.get_object('preferencesDialogSpinner')
    spinner.start()
    label = self.wTree.get_object('preferencesStatusLabel')
    label.set_text('checking settings...')
    ConfigChecker()
    newServer = self.wTree.get_object('preferencesServerComboBox').get_active_text()
    newDatabase = widget.get_active_text()
    print 'newDatabase is %s' % newDatabase
      
    if not newDatabase:
      newDatabase = ''
    
    model = widget.get_model()
    otherDatabases = set()
    iter = model.get_iter_first()
    while iter:
      print 'adding',model.get_value(iter,0)
      otherDatabases.add(model.get_value(iter,0))
      iter = model.iter_next(iter)
    
    try:  otherDatabases.remove(newDatabase)
    except KeyError: pass
    otherDatabases = list(otherDatabases)
    otherDatabases = string.join(otherDatabases, ',')
    print otherDatabases
    
    import ConfigParser
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))

    self.database = cfg.get('Phamerator','defaultDatabase')

    print "checking database: %s" % (newDatabase)
    valid = False
      
    sharedDatabase = Shared()
    sharedServer = Shared()
    serverCheckerEvnt = threading.Event()
    serverCheckerEvnt.clear()
    timeout = 10

    serverChecker = ServerDatabaseChecker(sharedServer, serverCheckerEvnt, newServer, timeout)
    serverChecker.start()
    
    while not serverCheckerEvnt.isSet():
      serverCheckerEvnt.wait(0.1)
      while gtk.events_pending():
        gtk.main_iteration(False)

    databaseCheckerEvnt = threading.Event()
    databaseCheckerEvnt.clear()
    
    databaseChecker = ServerDatabaseChecker(sharedDatabase, databaseCheckerEvnt, '%s/%s.sql' % (newServer, newDatabase), timeout)
    databaseChecker.start()
    
    while not databaseCheckerEvnt.isSet():
      databaseCheckerEvnt.wait(0.1)
      while gtk.events_pending():
        gtk.main_iteration(False)

    if sharedServer.status and sharedDatabase.status:
      print newServer + " is a valid server, adding to phamerator.conf"
      label.set_text('')
      valid = True

    elif sharedServer.status and not sharedDatabase.status:
      print newServer + " is a valid server, adding to phamerator.conf"
      label.set_text("database '%s' is not available on this server" % newDatabase)
      valid = True

    else:
      valid = False
      if newServer:
        label.set_text('cannot connect to server %s' % newServer)
      else:
        label.set_text('please add a server')
      print 'WARNING!  Cannot connect to server %s' % newServer

    cfg.set('Phamerator','otherDatabases', otherDatabases)
    cfg.set('Phamerator','defaultDatabase', newDatabase)
    #if valid:
    cfg_file = open(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'), 'w')
    cfg.write(cfg_file)
    cfg_file.close()
    spinner.stop()
    return

  def on_addServerButton_clicked(self, widget):
    ConfigChecker()
    d = AddServerDialog()
    serverName = d.run()
    import ConfigParser
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    self.server = cfg.get('Phamerator','defaultServer')

    if not serverName.startswith('http://'):
      serverName = 'http://%s' % serverName

    if not self.server.startswith('http://'):
      self.server = 'http://%s' % self.server

    try:
      otherServers = cfg.get('Phamerator','otherServers')
      otherServers = otherServers.split(',')

    except:
      otherServers = []
    serverDict = {}
    
    for item in otherServers:
      item = item.rstrip()
      item = item.lstrip()
      if item != "":
        serverDict[item] = 0
    
    adder = self.server.rstrip()
    adder = adder.lstrip()
    
    if (adder not in serverDict.keys()):
      serverDict[adder] = 0

    # if the new server is already the default server or in otherServers, do nothing

    if (serverName in serverDict.keys()):
      del serverDict[serverName]
      return
    # if the new name isn't a known server, make it the default server
    else:
      cbe = self.wTree.get_object("preferencesServerComboBox")
      cbe.prepend_text(serverName)
      model = cbe.get_model()
      cbe.set_active(0)

  def on_removeServerButton_clicked(self, widget):
    # delete the selected row from the combobox
    cbe = self.wTree.get_object('preferencesServerComboBox')
    oldserver = cbe.get_active_text()
    print 'removing %s' % oldserver
    model = cbe.get_model()
    if len(model) <= 1:
      print 'clearing model!'
      cbe.remove_text(0)
      model.clear()
      return
    iter = cbe.get_active_iter()
    if not iter:
      model.clear()
      newserver = ''
      return
    else:
      newiter = model.iter_next(iter)
      if not newiter:
        newiter = model.get_iter(0)
      newserver = model.get_value(newiter, 0)
    if not newiter:
      model.clear()
      return

    # delete the selected row from the config file and change the default to the new selected row
    #import ConfigParser
    #cfg = ConfigParser.RawConfigParser()
    #cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    #cfg.set('Phamerator','defaultServer', newserver)
    #print 'setting default server to %s' % newserver
    #otherServers = cfg.get('Phamerator','otherServers').replace(' ','')
    #cfg.set('Phamerator', 'otherServers', otherServers.replace(',%s' % oldserver, ''))
    #cfg_file = open(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'), 'w')
    #cfg.write(cfg_file)
    #cfg_file.close()

    # change the selection in the comboboxentry widget.  do this last to avoid conflicts
    # between this function and the on_preferencesServerComboBox_changed callback    
    if newiter:
      model.remove(iter)
      cbe.set_active_iter(newiter)
    else:
      model.clear()

  def on_addDatabaseButton_clicked(self, widget):
    print 'add database!'
    ConfigChecker()
    d = AddDatabaseDialog()
    databaseName = d.run()
    if databaseName: print databaseName
    else:
      return
    import ConfigParser
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    self.database = cfg.get('Phamerator','defaultDatabase')

    try:
      otherDatabases = cfg.get('Phamerator','otherDatabases')
      otherDatabases = otherDatabases.split(',')

    except:
      otherDatabases = []
    databaseDict = {}
    
    for item in otherDatabases:
      item = item.rstrip()
      item = item.lstrip()
      if item != "":
        databaseDict[item] = 0
    
    adder = self.database.rstrip()
    adder = adder.lstrip()
    
    if (adder not in databaseDict.keys()):
      databaseDict[adder] = 0

    if (databaseName in databaseDict.keys()):
      del databaseDict[databaseName]
      return
    # if the new name isn't a known database, make it the default database
    else:
      cbe = self.wTree.get_object("preferencesDatabaseComboBox")
      cbe.prepend_text(databaseName)
      model = cbe.get_model()
      print model

      cbe.set_active(0)

  def on_removeDatabaseButton_clicked(self, widget):
    print 'remove database!'
    # delete the selected row from the combobox
    cbe = self.wTree.get_object('preferencesDatabaseComboBox')
    oldDatabase = cbe.get_active_text()
    print 'removing %s' % oldDatabase
    model = cbe.get_model()
    if len(model) <= 1:
      print 'clearing model!'
      cbe.remove_text(0)
      model.clear()
      return
    iter = cbe.get_active_iter()
    if not iter:
      model.clear()
      newserver = ''
      return
    else:
      newiter = model.iter_next(iter)
      if not newiter:
        newiter = model.get_iter(0)
      newserver = model.get_value(newiter, 0)
    if not newiter:
      model.clear()
      return

    # change the selection in the comboboxentry widget.  do this last to avoid conflicts
    # between this function and the on_preferencesServerComboBox_changed callback    
    if newiter:
      model.remove(iter)
      cbe.set_active_iter(newiter)
    else:
      model.clear()

  def on_updateDatabaseButton_clicked(self, widget):
    print 'performing manual database update...'
    evnt = threading.Event()
    self.PManager.update_database(evnt, force=True)
    import glib
    glib.timeout_add_seconds(5, self.PManager.check_db_update_done, evnt)

  def change_window_title(self, title):
    window = self.PManager.wTree.get_object('mainWindow')
    window.set_title(title)

  def run(self):
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result


class Shared:
  def __init__(self):
    self.status = ''

class ServerDatabaseChecker(threading.Thread):
  def __init__(self, shared, evnt, url, timeout):
    threading.Thread.__init__(self)
    self.shared = shared
    self.evnt = evnt
    self.url = url
    self.timeout = timeout
  def run(self):
    print 'checking %s' % self.url
    try:
      f = urllib2.urlopen('%s' % (self.url), timeout=self.timeout)
      self.shared.status = True
    except:
      self.shared.status = False
    print 'THREAD returning %s' % self.shared.status
    self.evnt.set()

class AddServerDialog():
  def __init__(self):
    #Dialog.__init__(self)
    print 'add server!'
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "addServerDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["addServerDialog"])
    self.dlg = self.wTree.get_object("addServerDialog")
    self.result = self.dlg.run()
    text = self.wTree.get_object("addServerEntry").get_text()
    self.dlg.destroy()
    if not self.result:
      return None
    else:
      return text

class AddDatabaseDialog():
  def __init__(self):
    #Dialog.__init__(self)
    print 'add database!'
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "addDatabaseDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["addDatabaseDialog"])
    self.dlg = self.wTree.get_object("addDatabaseDialog")
    self.result = self.dlg.run()
    text = self.wTree.get_object("addDatabaseEntry").get_text()
    self.dlg.destroy()
    if not self.result:
      return None
    else:
      return text
      
class NewDatabaseAvailableDialog():
  def __init__(self):
    pass
  def run(self):
    self.gladefile = gladeFile().filename
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["newDatabaseAvailableDialog"])
    self.dlg = self.wTree.get_object("newDatabaseAvailableDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()
    return self.result

class AddPhageDialog:
  """This class is used to show AddPhageDialog"""
  def __init__(self, name=''):
    #setup the phage that we will return
    self.phage = Phage()
    self.logger = logger.logger(True)

  def run(self):
    """This function will show the addPhageDialog"""  
    #load the dialog from the glade file    
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "AddPhageDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["AddPhageDialog"])
    #Get the actual dialog widget
    self.dlg = self.wTree.get_object("AddPhageDialog")
    #Get all of the Entry Widgets and set their text
    self.enName = self.wTree.get_object("AddPhage_EnterName")
    self.allowRefSeqsCheckBox = self.wTree.get_object("allowRefSeqsCheckBox")
  
    #run the dialog and store the response
    self.result = self.dlg.run()
    #get the value of the entry fields
    self.phage.name = self.enName.get_text()
    #we are done with the dialog, destroy it
    self.dlg.destroy()
    if self.result == gtk.RESPONSE_CANCEL: return None
    self.logger.log('destroying AddPhageDialog')
    #return the result and the phage
    return (self.result,self.phage,self.allowRefSeqsCheckBox.get_active())

class SaveDialog(Dialog):
  """Generic dialog for phamerator file-saving operations"""
  def __init__(self, name):
    print 'creating saveDialog'
    #Dialog.__init__(self)
    self.gladefile = gladeFile().filename
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, [name])
    self.current_folder = os.path.join(os.environ['HOME'], 'Desktop')
    if name is not None: self.wTree.get_object(name).set_current_folder(self.current_folder)
  def get_chooser_filename(self, chooser):
    filename = chooser.get_filename()
    choices = ['','svg','pdf','ps', 'png']
    combo = self.wTree.get_object('saveAsComboBox')
    ext = choices[combo.get_active()]
    if not ext:
      ext = filename.split('.')[-1]
      if ext not in ['svg', 'pdf', 'ps', 'png']:
        ext = None
    return filename, ext

class InvalidConfigurationDialog(Dialog):
  """This class is used to show the InvalidConfigurationDialog"""
  def __init__(self):
    #setup the glade file
    pass
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "InvalidConfigurationDialog")
    #self.dlg = self.wTree.get_object("InvalidConfigurationDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["InvalidConfigurationDialog"])
    self.dlg = self.wTree.get_object("InvalidConfigurationDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class AboutDialog(Dialog):
  """This class is used to show AboutDialog"""
  def __init__(self):
    #setup the glade file
    pass
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "AboutDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["AboutDialog"])
    self.dlg = self.wTree.get_object("AboutDialog")

    try:
      from bzrlib.branch import Branch
      my_branch = Branch.open(os.path.join(os.path.dirname(__file__), '../..'))
      version = my_branch.last_revision_info()[0]
      self.dlg.set_comments('you are using a development version')
    except:
      self.dlg.set_comments('')
      version = open(os.path.join(os.path.dirname(__file__), '../..', 'README.txt')).readlines()[0].split(' ')[-1]

    self.dlg.set_version('%s' % version)
    self.result = self.dlg.run()
    self.dlg.destroy()

class WhatsNewDialog(Dialog):
  """This class is used to show WhatsNewDialog"""
  def __init__(self):
    pass
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "whatsNewDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["whatsNewDialog"])
    self.dlg = self.wTree.get_object("whatsNewDialog")
    self.textView = self.wTree.get_object('whatsNewDialogTextView')
    buffer = gtk.TextBuffer()
    self.textView.set_buffer(buffer)
    
    try:
      from bzrlib.branch import Branch
      my_branch = Branch.open(os.path.join(os.path.dirname(__file__), '../..'))
      rev_ids = my_branch.revision_history()
      rev_ids.reverse()
      repo = my_branch.repository
      for rev_id in rev_ids:
        revision=repo.get_revision(rev_id)
        buffer.insert_at_cursor('revision ')
        buffer.insert_at_cursor(str(my_branch.revision_id_to_revno(rev_id)))
        buffer.insert_at_cursor(' :: ')
        buffer.insert_at_cursor(revision.message)
        buffer.insert_at_cursor('\n\n')
    except:
      pass

    self.result = self.dlg.run()
    self.dlg.destroy()

class DbStatsDialog(Dialog):
  """This class is used to show DbStatsDialog"""
  def __init__(self,c):
    self.c = c

  def show_number_of_genes(self):
    n = get_number_of_genes(self.c)
    genesLabel = self.wTree.get_object("genesLabel")
    genesLabel.set_text('Genes (%s)' % n)
    
  def show_number_of_genomes(self):
    n = get_number_of_genomes(self.c)
    genomesLabel = self.wTree.get_object("genomesLabel")
    genomesLabel.set_text('Genomes (%s)' % n)
 
  def show_number_of_phamilies(self):
    n = get_number_of_phamilies(self.c)
    phamiliesLabel = self.wTree.get_object("phamiliesLabel")
    phamiliesLabel.set_text('Phamilies (%s)' % n)
 
  def show_genome_length_min(self):
    phage, length = get_shortest_genome(self.c)
    GenomeLengthMin = self.wTree.get_object("GenomeLengthMin")
    GenomeLengthMin.set_text("%s bp (%s)" % (length, phage))

  def show_genome_length_max(self):
    phage, length = get_longest_genome(self.c)
    GenomeLengthMax = self.wTree.get_object("GenomeLengthMax")
    GenomeLengthMax.set_text("%s bp (%s)" % (length, phage))

  def show_genome_length_mean(self):
    length = get_mean_genome_length(self.c)
    GenomeLengthMean = self.wTree.get_object("GenomeLengthMean")
    GenomeLengthMean.set_text("%s bp" % length)

  def show_genome_gc_min(self):
    pass
  def show_genome_gc_max(self):
    pass
  def show_genome_gc_mean(self):
    pass
  def show_gene_length_min(self):
    phage, gene, length = get_shortest_gene(self.c)
    GeneLengthMin = self.wTree.get_object("GeneLengthMin")
    GeneLengthMin.set_text("%s bp (%s %s)" % (length, phage, gene))


  def show_gene_length_max(self):
    phage, gene, length = get_longest_gene(self.c)
    GeneLengthMax = self.wTree.get_object("GeneLengthMax")
    GeneLengthMax.set_text("%s bp (%s %s)" % (length, phage, gene))


  def show_gene_length_mean(self):
    length = get_mean_gene_length(self.c)
    GeneLengthMean = self.wTree.get_object("GeneLengthMean")
    GeneLengthMean.set_text("%s bp" % length)


  def show_gene_gc_min(self):
    pass
  def show_gene_gc_max(self):
    pass
  def show_gene_gc_mean(self):
    pass
  def show_phamily_size_min(self):
    # name is a list containing the names of all phams of size 'size'
    name, size = get_smallest_pham_size(self.c)
    PhamilySizeMin = self.wTree.get_object("PhamilySizeMin")
    if len(name) > 1:
      PhamilySizeMin.set_text("%s phams of size %s" % (len(name), size))
    else:
      PhamilySizeMin.set_text("size=%s(phamily=%s)" % (size, name))

  def show_phamily_size_max(self):
    # name is a list containing the names of all phams of size 'size'
    name, size = get_largest_pham_size(self.c)
    PhamilySizeMax = self.wTree.get_object("PhamilySizeMax")
    if len(name) > 1:
      PhamilySizeMax.set_text("%s phams of size %s" % (len(name), size))
    else:
      PhamilySizeMax.set_text("%s (phamily %s)" % (size, str(int(name[0][0]))))

  def show_phamily_size_mean(self):
    size = get_mean_pham_size(self.c)
    PhamilySizeMean = self.wTree.get_object("PhamilySizeMean")
    PhamilySizeMean.set_text("%s" % size)

  def show_phamily_gc_min(self):
    pass
  def show_phamily_gc_max(self):
    pass
  def show_phamily_gc_mean(self):
    pass

  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "dbStatsDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["dbStatsDialog"])

    self.show_number_of_genes()
    self.show_number_of_genomes()
    self.show_number_of_phamilies()
    self.show_genome_length_min()
    self.show_genome_length_max()
    self.show_genome_length_mean()
    self.show_gene_length_min()
    self.show_gene_length_max()
    self.show_gene_length_mean()
    self.show_phamily_size_min()
    self.show_phamily_size_max()
    self.show_phamily_size_mean()

    self.dlg = self.wTree.get_object("dbStatsDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class ErrorAddingPhageDialog(Dialog):
  """This class is used to show ErrorAddingPhageDialog, usually when user tries
  to add a phage that is already in the database"""
  def __init__(self, errorMessage='Could not add phage to database'):
    self.msg = errorMessage
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "ErrorAddingPhageDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["ErrorAddingPhageDialog"])
    self.dlg = self.wTree.get_object("ErrorAddingPhageDialog")
    errTextView = self.wTree.get_object("errorAddingPhageTextView") # errorAddingPhageTextView
    errText = gtk.TextBuffer(table=None)
    errText.set_text(self.msg)
    errTextView.set_buffer(errText)
    self.result = self.dlg.run()
    self.dlg.destroy()
    return self.result

class PhageChooserDialog(Dialog):
  """This class is used to present a list of phages to the user when more than one result
  was returned from using the 'Add' button.  The user must choose a phage from the list
  or cancel the 'Add' attempt."""
  def __init__(self, results):
    self.gi_list = results
    self.gladefile = gladeFile().filename
    self.active = None
  def callback(self, widget, data=None):
    self.active = data
  def run(self):
    from Bio import Entrez, SeqIO
    #self.wTree = gtk.glade.XML(self.gladefile, "phageChooserDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["phageChooserDialog"])
    self.dlg = self.wTree.get_object("phageChooserDialog")
    box = self.wTree.get_object('pickAddPhageResultBox')

    radio_button = None
    for n, gi in enumerate(self.gi_list):
      handle = Entrez.efetch(db='nucleotide', id=gi, rettype='gb')
      record = SeqIO.read(handle, 'genbank')
      radio_button = gtk.RadioButton(group=radio_button, label=record.description)
      radio_button.connect("toggled", self.callback, record)
      if n == 0:
        radio_button.set_active(True)
        self.callback(None, record)
      radio_button.show()
      box.pack_start(radio_button, False, False, 0)
    box.show_all()
    r=self.dlg.run()
    self.dlg.destroy()
    if r == gtk.RESPONSE_OK:
      return self.active
    else:
      return None

class batchFileSaveAsDialog(SaveDialog):
  """This class is used to show the batchFileSaveAsDialog, when a user wants to save a 
  bunch of images in a non-interactive way"""
  def __init__(self, pM):
    SaveDialog.__init__(self, "batchFileSaveAsDialog")
    self.gladefile = gladeFile().filename
    dic = {"on_appendDateCheckButton_toggled" : self.on_appendDateCheckButton_toggled}
    self.wTree.connect_signals(dic)
    self.chooser = self.wTree.get_object("batchFileSaveAsDialog")
    #self.chooser.set_current_name('pham####')
    self.pM = pM

  def on_appendDateCheckButton_toggled(self, widget):
    appendButton = self.wTree.get_object('appendDateCheckButton')
    today = date.today()
    currentName = os.path.split(self.chooser.get_filename())[-1]
    if appendButton.get_active():
      currentName = '%s-%s' % (currentName,today)
    else:
      currentName = currentName.replace('-%s' % today, '')

  def run(self):
    combo = self.wTree.get_object('saveAsComboBox')
    combo.set_active(0)
    cols = self.pM.dataTreeView.get_columns()
    mapType = cols[0].get_title()
    if mapType == 'Phamily':
      treeSelection = self.pM.dataTreeView.get_selection()
      (model, pathlist) = treeSelection.get_selected_rows()
      phamsToSave = []
      for path in pathlist:
        iter = model.get_iter(path)
        phamName = str(model.get_value(iter,0))
        phamsToSave.append(phamName)
    else: print 'Phamily not selected'

    response = self.chooser.run()

    if response == gtk.RESPONSE_OK:
      dirname, ext = self.get_chooser_filename(self.chooser)
      if not ext: ext = 'pdf'
      
      for phamName in phamsToSave:
        filename = 'pham' + phamName + '.' + ext
        self.pM.draw_phamCircle_canvas(phamName=phamName)

        self.pM.phamCircleCanvas.props.automatic_bounds = True
        x1, y1, x2, y2 = self.pM.phamCircleCanvas.get_bounds()
        x, y = int(x2-x1)+240, int(y2-y1)+240

        #self.pM.phamCircleCanvas.set_bounds(0,0, 10000, 10000)
        filename = os.path.join(dirname, filename)
        if ext == 'svg':
          surface = cairo.SVGSurface (filename, x,y)
        elif ext == 'pdf':
          surface = cairo.PDFSurface (filename, x,y)
        elif ext == 'ps':
          surface = cairo.PSSurface (filename, x,y)
        elif ext == 'png':
          surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, x,y)

        cr = cairo.Context (surface)

        # center in the page (9x10)
        cr.translate (36, 130)
        self.pM.phamCircleCanvas.render (cr, None, 0.1)
        cr.show_page ()
        if ext == 'png': surface.write_to_png(filename)
    elif response == gtk.RESPONSE_CANCEL:
      pass
    self.chooser.destroy()

class BLASTWarningDialog(Dialog):
  """This class is used to show the BLASTWarningDialog"""
  def __init__(self):
    self.gladefile = gladeFile().filename
    import gconf
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    hideDialog = self.client.get_bool('/apps/phamerator/hide_BLAST_warning_dialog')

  def run(self):
    import gconf
    hideDialog = self.client.get_bool('/apps/phamerator/hide_BLAST_warning_dialog')

    if hideDialog: return
    self.client.set_bool('/apps/phamerator/hide_BLAST_warning_dialog', True)
    print 'trying to set hideBLASTWarningDialog to True'
    #self.wTree = gtk.glade.XML(self.gladefile, "BLASTWarningDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["BLASTWarningDialog"])
    self.dlg = self.wTree.get_object("BLASTWarningDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class accountCreationSuccessDialog(Dialog):
  """This class is used to show the accountCreationSuccessDialog"""
  def run(self):
    #self.wTree = gtk.glade.XML(self.gladefile, "accountCreationSuccessDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["accountCreationSuccessDialog"])
    self.dlg = self.wTree.get_object("accountCreationSuccessDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class accountCreationErrorDialog(Dialog):
  """This class is used to show the accountCreationErrorDialog"""
  def __init__(self):
    Dialog.__init__(self)
    #self.wTree = gtk.glade.XML(self.gladefile, "accountCreationErrorDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["accountCreationErrorDialog"])

  def run(self):
    self.dlg = self.wTree.get_object("accountCreationErrorDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class databaseSetupWarningDialog(Dialog):
  """This class is used to show the databaseSetupWarningDialog"""
  def __init__(self, dbname):
    print 'open database setup dialog'
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "databaseSetupWarningDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["databaseSetupWarningDialog"])
    self.dbname = self.wTree.get_object("databaseSetupWarningDbname")
    self.dbname.set_text(dbname)
  def run(self):
    print 'run database setup dialog'
    self.dlg = self.wTree.get_object("databaseSetupWarningDialog")
    self.dlg.set_default_response(gtk.RESPONSE_OK)
    self.result = self.dlg.run()
    self.pwd = self.wTree.get_object("databaseSetupWarningPassword").get_text()
    self.dbname = self.wTree.get_object("databaseSetupWarningDbname").get_text()
    self.dlg.destroy()
    return self.result

class databaseConnectionErrorDialog(Dialog):
  """This class is used to show the databaseConnectionErrorDialog"""
  def __init__(self, error):
    print error
    errno, errmsg = error
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "databaseConnectionErrorDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["databaseConnectionErrorDialog"])

    label = self.wTree.get_object("databaseConnectionErrorLabel")
    label.set_text('%s: %s' % (errno, errmsg))
  def run(self):
    self.dlg = self.wTree.get_object("databaseConnectionErrorDialog")
    self.result = self.dlg.run()
    self.dlg.destroy()

class OpenGenBankFileDialog:
  """This class is used to show the file dialog needed to select a GenBank file to add to the database"""
  def __init__(self):
    #setup the phage that we will return
    self.logger = logger.logger(True)
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "OpenGenBankFileDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["OpenGenBankFileDialog"])
    self.dlg = self.wTree.get_object("OpenGenBankFileDialog")
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result

class ExportFastaDialog(Dialog):
  def __init__(self):
    Dialog.__init__(self, 'exportFastaDialog')

  def run(self):
    self.dlg = self.wTree.get_object("exportFastaDialog")
    self.result = self.dlg.run()
    #self.set_current_folder(os.path.split(self.dlg.get_filename()[-2:-1]))
    self.dlg.hide()
    return self.result

     # if the user didn't cancel
      # get the selected filename
      # get the data from the database
      # if the file doesn't already exist:
        # write it 
      # else:
        # go back to open the file chooser   

class ExportPhamTableDialog(Dialog):
  def __init__(self):
    Dialog.__init__(self, "phamTableFileChooserDialog")
    #self.wTree = gtk.glade.XML(self.gladefile, "phamTableFileChooserDialog")
  def run(self):
    self.dlg = self.wTree.get_object("phamTableFileChooserDialog")
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result

class ExportClusterTableDialog(Dialog):
  def __init__(self):
    Dialog.__init__(self, "phamTableFileChooserDialog")
    #self.wTree = gtk.glade.XML(self.gladefile, "phamTableFileChooserDialog")
  def run(self):
    self.dlg = self.wTree.get_object("phamTableFileChooserDialog")
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result

class ExportFastaNucleotideDialog(Dialog):
  def __init__(self):
    Dialog.__init__(self, "exportFastaNucleotideDialog")
    #self.wTree = gtk.glade.XML(self.gladefile, "exportFastaNucleotideDialog")
  def run(self):
    self.dlg = self.wTree.get_object("exportFastaNucleotideDialog")
    self.result = self.dlg.run()
    self.extra = int(self.wTree.get_object('extraNucleotidesSpinButton').get_value())
    self.dlg.hide()
    return self.result, self.extra

class ExportFastaGenomeDialog(Dialog):
  def __init__(self):
    Dialog.__init__(self, "exportFastaGenomeDialog")
    #self.wTree = gtk.glade.XML(self.gladefile, "exportFastaGenomeDialog")
  def run(self):
    self.dlg = self.wTree.get_object("exportFastaGenomeDialog")
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result

class BlastDownloadDialog:
  def __init__(self,showPopUp=True,filePath=None):
    self.gladefile = gladeFile().filename
    self.wTree = gtk.Builder()
    dic = {"on_specifyButton_activate" : self.on_specifyButton_activate,"on_downloadSpecificPathButton_activate":self.on_downloadSpecificPathButton_activate, "on_okbutton_activate":self.on_okbutton_activate}

    self.wTree.add_objects_from_file(self.gladefile, ["blastDownloadDialog"])
    self.wTree.connect_signals(dic)
    self.dlg = self.wTree.get_object("blastDownloadDialog")

  def on_okbutton_activate(self,widget):
    if self.wTree.get_object("downloadRadio").get_active() == True:
      self.info = "download:defaultLocation"
    elif self.wTree.get_object("specifyRadio").get_active()==True:
      if self.isGoodFilePath == True:
        self.info = "existing:" + self.filePath
      else:
        self.on_specifyButton_activate(None)
    elif self.wTree.get_object("downloadSpecificPathRadio").get_active()==True:
      if self.filePath != None:
        self.info = "download:" + self.filePath
      else:
        self.on_downloadSpecificPathButton_activate(None)

  def on_downloadSpecificPathButton_activate(self,widget):
    self.wTree.get_object("downloadSpecificPathRadio").set_active(True)
    self.dlg.hide()
    fileChooser = BlastCustomLocationDialog()
    result = fileChooser.run()
    if result == gtk.RESPONSE_OK:
      fname = fileChooser.dlg.get_filename()
      self.filePath = fname
      self.info = "download:" + self.filePath
    else:
      self.run()
 
  def on_specifyButton_activate(self,widget):
    self.wTree.get_object("specifyRadio").set_active(True)
    self.dlg.hide()
    fileChooser = OpenBlastFolderDialog()
    result = fileChooser.run()
    if result == gtk.RESPONSE_OK:
      fname = fileChooser.dlg.get_filename()
      blast_dir = fname
      if os.path.exists(os.path.join(blast_dir,'bin','bl2seq')):
        self.isGoodFilePath = True
        self.filePath = blast_dir
        #self.wTree.get_object("specifyImage").hide()
        #self.wTree.get_object("specifyLabel").hide()
        self.info = "existing:" + self.filePath
      else:
        md = gtk.MessageDialog(parent=None,flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_CLOSE, message_format="The location you selected does not contain the BLAST binaries.\nPlease try again or make a new selection.")
        md.run()
        md.destroy()
        self.run()
    else:
      self.run()

  def run(self):
    self.result = self.dlg.run()
    self.dlg.destroy()
    while gtk.events_pending():
      gtk.main_iteration(False)
    return self.result

class BlastCustomLocationDialog:
  def __init__(self):
    print "opening blastCustomLocationDialog"
  def run(self):
    self.gladefile = gladeFile().filename
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["blastCustomLocationDialog"])
    self.dlg = self.wTree.get_object("blastCustomLocationDialog")
    self.dlg.set_current_folder(os.environ['HOME'])
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result

class OpenBlastFolderDialog:
  def __init__(self):
    pass
  def run(self):
    self.gladefile = gladeFile().filename
    #self.wTree = gtk.glade.XML(self.gladefile, "openBlastFolderDialog")
    self.wTree = gtk.Builder()
    self.wTree.add_objects_from_file(self.gladefile, ["openBlastFolderDialog"])
    self.dlg = self.wTree.get_object("openBlastFolderDialog")
    self.dlg.set_current_folder(os.environ['HOME'])
    self.result = self.dlg.run()
    self.dlg.hide()
    return self.result
