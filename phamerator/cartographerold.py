import os, sys, colorsys
from os.path import join, getsize
import ConfigParser
import random
import gobject
import gtk
import pango
import gconf
import goocanvas, cairo
#import canvasItems
#import db_conf, gene, pham
from phamerator import db_conf, gene, pham, phamerator_manage_db
from phamerator_manage_db import *

def main(argv):
  window = gtk.Window()
  window.set_default_size(640, 600)
  window.show()
  window.connect("delete_event", on_delete_event)
  
  scrolled_win = gtk.ScrolledWindow()
  scrolled_win.set_shadow_type(gtk.SHADOW_IN)
  scrolled_win.show()
  window.add(scrolled_win)
 
  # FIXME: need to specify username, password, server, and database
  c = db_conf.db_conf().get_cursor()
  PhageID = get_PhageID_from_name(c, sys.argv[1])
  length = get_length_of_genome(c, PhageID)
  #print length
  
  #canvas = goocanvas.CanvasView()
  canvas = goocanvas.Canvas()
  canvas.props.automatic_bounds = True
  canvas.background_color = 'white'
  #canvas.set_size_request(600, 200)
  #canvas.set_bounds(0, 0, float(length)/200, 60)
  #canvas.set_bounds(0, 0, float(length)/10, 600)
  canvas.show()
  scrolled_win.add(canvas)
  
  canvas.connect("item-created", on_item_created)

  ## Create the canvas model

  self.root = goocanvas.GroupModel()
  self.set_root_item_model(self.root)
  gtk.main()

class phameratorGroupModel(goocanvas.GroupModel):
  def __init__(self, *args, **kwargs):
    super(goocanvas.GroupModel, self).__init__ (*args, **kwargs)
    self.x = 0
    self.y = 0

  def translate(self, x, y):
    self.x = self.x + x
    self.y = self.y + y
    #print '[%s,%s]' % (self.x, self.y)
    super(phameratorGroupModel, self).translate(x, y)

class CanvasController:
  def __init__(self,c, mapWTree, interface):
    print 'init CanvasController'
    self.c = c
    self.mapWTree = mapWTree
    self.DNATextView = mapWTree.get_object('DNATextView')
    self.DNATextView.set_wrap_mode(gtk.WRAP_CHAR)
    self.ProteinTextView = mapWTree.get_object('ProteinTextView')
    self.ProteinTextView.set_wrap_mode(gtk.WRAP_CHAR)
    #self.assign_interface(interface)
    self.DNATextBuffer = self.DNATextView.get_buffer()
    self.ProteinTextBuffer = self.ProteinTextView.get_buffer()
    self.client = gconf.client_get_default()
    checkBox = self.mapWTree.get_object('show_phamily_names_checkBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/show_pham_names'))
    checkBox = self.mapWTree.get_object('shorten_description_checkBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/shorten_description'))
    checkBox = self.mapWTree.get_object('show_description_checkBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/show_description'))
    checkBox = self.mapWTree.get_object('show_domains_checkBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/show_domains'))
    checkBox = self.mapWTree.get_object('hover_highlights_pham_checkBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/hover_highlights_pham'))
    checkBox = self.mapWTree.get_object('blastAlignmentCheckBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/show_alignment'))
    checkBox = self.mapWTree.get_object('eValuesCheckBox')
    checkBox.set_active(self.client.get_bool('/apps/phamerator/show_alignment_text'))
    
    if self.client.get_bool('/apps/phamerator/show_alignment'):
      checkBox.set_sensitive(True)
    else:
      checkBox.set_sensitive(False)
      self.client.set_bool('/apps/phamerator/show_alignment_text', False)

    gene_color = self.client.get_string('/apps/phamerator/gene_color')
    try: self.mapWTree.get_object(gene_color).set_active(True)
    except: self.mapWTree.get_object('color_by_phamily').set_active(True)

  def assign_interface(self, interface):
    self.interface = interface
    interface.controller = self
  def gene_selection_changed(self, selectedItems):
    # get the nt and aa sequences and stick them in the boxes
    GeneIDs = []
    for s in selectedItems:
      GeneIDs.append(s.get_model().get_data("GeneID"))
    self.interface.show_gene_sequences(GeneIDs)

  def scan_for_plugins(self):
    '''look in the plugin directory (~/.phamerator/plugins) for plugins'''
    pluginDir = os.environ['HOME'] + '.phamerator/plugins'
    print 'scanning for plugins in %s' % pluginDir

    for module in os.listdir(pluginDir):
      if module in ('.', '..'): continue # ignore these in the directory listing
      for file in os.listdir(module):
        if file == '__init__.py':
          plugin = canvasPlugin(module)

class canvasPlugin:
  '''this class is intended to be subclassed by plugins, who will use it to draw on the genome canvas'''
  def __init__(self, module):
    '''instances get a reference to the db cursor and canvas from the CanvasInterface'''
    self.c = None
    self.canvas = None # how do I get this from phageManager App()?
    self.register(module)
  def register():
    '''make the App() aware of this plugin'''
    pass
    # do something, but what?
  def unregister():
    '''make the App() unaware of this plugin'''
    pass

class geneModel(goocanvas.RectModel):
  def __init__(self, *args, **kwargs):
    super (geneModel, self).__init__ (*args, **kwargs)
    self.set_data('width', kwargs['width'])
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    self.client.notify_add('/apps/phamerator/gene_color', self.change_color)

    color_by = self.client.get_string('/apps/phamerator/gene_color')
    if color_by == 'no_color':
      self.props.fill_color = 'white'

  def change_color(self, client, *args, **kwargs):
    color_by = self.client.get_string('/apps/phamerator/gene_color')
    if color_by == 'no_color':
      self.client.set_string('/apps/phamerator/gene_color', 'no_color')
      self.props.fill_color = 'white'
    elif color_by == 'color_by_phamily':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_phamily')
      self.props.fill_color = self.get_data('phamily_color')
    elif color_by == 'color_by_gc':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_gc')
      self.props.fill_color = self.get_data('gc_color')
    elif color_by == 'color_by_abundance':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_abundance')
      self.props.fill_color = self.get_data('abundance_color')
    elif color_by == 'color_by_cluster_conservation':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_cluster_conservation')
      self.props.fill_color = self.get_data('cluster_conservation_color')      

class domainModel(goocanvas.RectModel):
  def __init__(self, *args, **kwargs):
    super (domainModel, self).__init__ (*args, **kwargs)
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    #super (PolylineModelListener, self).__init__ (*args, **kwargs)

    self.client.notify_add('/apps/phamerator/show_domains', self.show_domains)
    self.show_domains(self.client)

  def show_domains(self, client, *args, **kwargs):
    if self.client.get_bool('/apps/phamerator/show_domains'):
      self.props.visibility = goocanvas.ITEM_VISIBLE
    else:
      self.props.visibility = goocanvas.ITEM_INVISIBLE


  def change_color(self, client, *args, **kwargs):
    color_by = self.client.get_string('/apps/phamerator/gene_color')
    if color_by == 'no_color':
      self.client.set_string('/apps/phamerator/gene_color', 'no_color')
      self.props.fill_color = 'white'
    elif color_by == 'color_by_phamily':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_phamily')
      self.props.fill_color = self.get_data('phamily_color')
    elif color_by == 'color_by_cluster_conservation':
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_cluster_conservation')
      self.props.fill_color = self.get_data('cluster_conservation_color')


class PhamNameLabel(goocanvas.TextModel):
  def __init__(self, *args, **kwargs):
    super (PhamNameLabel, self).__init__ (*args, **kwargs)
    #goocanvas.RectModel.__init__(self)
    self.client = gconf.client_get_default()
    #self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    self.client.notify_add('/apps/phamerator/show_pham_names', self.show_pham_names)
    if self.client.get_bool('/apps/phamerator/show_pham_names'):
      self.props.visibility = goocanvas.ITEM_VISIBLE
    else:
      self.props.visibility = goocanvas.ITEM_INVISIBLE

  def show_pham_names(self, client, *args, **kwargs):
    #print 'show_pham_names called'
    show_pham_names = self.client.get_bool('/apps/phamerator/show_pham_names')
    if    show_pham_names: self.props.visibility = goocanvas.ITEM_VISIBLE
    else: self.props.visibility = goocanvas.ITEM_INVISIBLE

class GeneDescriptionLabel(goocanvas.TextModel):
  def __init__(self, *args, **kwargs):
    super (GeneDescriptionLabel, self).__init__ (*args, **kwargs)
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    self.client.notify_add('/apps/phamerator/shorten_description', self.shorten_description)
    self.client.notify_add('/apps/phamerator/show_description', self.show_description)
    if self.client.get_bool('/apps/phamerator/shorten_description'):
      self.props.ellipsize=pango.ELLIPSIZE_END
      #self.props.ellipsize = True
    else:
      self.props.ellipsize=pango.ELLIPSIZE_NONE
      #self.props.ellipsize = False
    self.show_description(self.client)

  def shorten_description(self, client, *args, **kwargs):
    #print 'shorten_description called'
    shorten_description = self.client.get_bool('/apps/phamerator/shorten_description')
    if shorten_description:
      self.props.ellipsize=pango.ELLIPSIZE_END
      #self.props.ellipsize = True
    else: self.props.ellipsize = pango.ELLIPSIZE_NONE
  
  def show_description(self, client, *args, **kwargs):
    if self.client.get_bool('/apps/phamerator/show_description'):
      self.props.visibility = goocanvas.ITEM_VISIBLE
    else:
      self.props.visibility = goocanvas.ITEM_INVISIBLE

class PolylineModelListener(goocanvas.PolylineModel):
  def __init__(self, *args, **kwargs):
    super (PolylineModelListener, self).__init__ (*args, **kwargs)
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)

    self.client.notify_add('/apps/phamerator/show_alignment', self.show_alignment)
    self.show_alignment(self.client)

  def show_alignment(self, client, *args, **kwargs):
    if self.client.get_bool('/apps/phamerator/show_alignment'):
      self.props.visibility = goocanvas.ITEM_VISIBLE
    else:
      self.props.visibility = goocanvas.ITEM_INVISIBLE

class BlastAlignmentLabel(goocanvas.TextModel):
  def __init__(self, *args, **kwargs):
    super (BlastAlignmentLabel, self).__init__ (*args, **kwargs)
    self.set_data('type', 'blastAlignmentLabel')
    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    self.client.notify_add('/apps/phamerator/show_alignment_text', self.show_alignment_text)
    self.show_alignment_text(self.client)

  def show_alignment_text(self, client, *args, **kwargs):
    show_alignment_text = self.client.get_bool('/apps/phamerator/show_alignment_text')
    if show_alignment_text:
      self.props.visibility = goocanvas.ITEM_VISIBLE
    else:
      self.props.visibility = goocanvas.ITEM_INVISIBLE
      
class ColorConverter:
  def e_value_to_color(self, e_value):
    e = "%e" % e_value
    exp = abs(int(e.split('e')[-1]))
    if int(exp) == 0: # just in case e value is actually zero
      hue = 1.0
    else:
      hue = exp/200.0 # e values seem to round to zero once they get below 1e-200

    hue = min(hue,0.75) # otherwise hsv(1,0.8,0.8) and hsv(0,0.8,0.8) translate to the same rgb value
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    #rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    #return '#%02x%02x%02x' % rgb
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    return int('%#02x%02x%02x' % rgb, 16)
    
  def e_value_to_color_rgba(self, e_value):
    e = "%e" % e_value
    exp = abs(int(e.split('e')[-1]))
    if int(exp) == 0: # just in case e value is actually zero
      hue = 1.0
    else:
      hue = exp/200.0 # e values seem to round to zero once they get below 1e-200

    hue = min(hue,0.75) # otherwise hsv(1,0.8,0.8) and hsv(0,0.8,0.8) translate to the same rgb value
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    #rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    #return '#%02x%02x%02x' % rgb
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255,50.0) # was 100.0
    return int('%#02x%02x%02x%02x' % rgb, 16)  

  def GC_to_color(self, GC):
    scaledGC = max(0, GC-52.0)
    scaledGC = min(15, scaledGC)
    value = scaledGC/15.0
    #value = GC/100.0
    #hue = min(hue,0.75) # otherwise hsv(1,0.8,0.8) and hsv(0,0.8,0.8) translate to the same rgb value
    if GC > 65:
      rgb = colorsys.hsv_to_rgb(0.33, 1.0, value)
    elif GC< 55:
      rgb = colorsys.hsv_to_rgb(0.33, 0.0, value)
    else:
      rgb = colorsys.hsv_to_rgb(0.33, 0.5, value)
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    return '#%02x%02x%02x' % rgb

  def gene_abundance_to_color(self, abundance, largestPhamSize):
    largestPhamSize = float(largestPhamSize)
    abundance = float(abundance)
    scaledAbundance = abundance/largestPhamSize
    rgb = colorsys.hsv_to_rgb(0.66, 0.0, 1-min(1,(5*scaledAbundance))) #(scaledAbundance+(abundance/largestPhamSize))) # orphams should be white for consistency
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    return '#%02x%02x%02x' % rgb
    
  def gene_cluster_conservation_to_color(self, intra_conservation, inter_conservation):
    # @cluster: a value like "A", "B1", or None
    # @intra_conservation: is the gene in some or all of the genomes in this cluster
    # @inter_conservation: is the gene in none, some, or all of the genomes NOT in this cluster
    if intra_conservation == 'some':
      if not inter_conservation:
        rgb = colorsys.hsv_to_rgb(0.15, 1.0, 1.0) # some, None: Yellow?
      elif inter_conservation == 'some':
        rgb = colorsys.hsv_to_rgb(0.3, 1.0, 0.6)  # some, some: Green
      elif inter_conservation == 'all':
        rgb = colorsys.hsv_to_rgb(0.45, 1.0, 1.0) # some, all: N/D
    if intra_conservation == 'all':
      if not inter_conservation:
        rgb = colorsys.hsv_to_rgb(0.0, 1.0, 1.0)  # all, None: Blue
      elif inter_conservation == 'some':
        rgb = colorsys.hsv_to_rgb(0.75, 1.0, 1.0) # all, some: Purple
      elif inter_conservation == 'all':
        rgb = colorsys.hsv_to_rgb(0.9, 1.0, 1.0)  # all, all: N/D
    rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
    return '#%02x%02x%02x' % rgb

class BlastAlignmentModel:
  def __init__(self, group, query, query_start, query_end, subject, subject_start, subject_end,
               e_value, zoomFactor, height):
    #print 'adding blast result at %s, %s, %s, %s, %s, %s' % (query_start, query_end, subject_start, subject_end, zoomFactor, height)
    #print 'query: %s :: subject: %s' % (query, subject)
    #parent = group
    close_path = True
    stroke_color = "black"
    fill_color = "yellow"
    cc = ColorConverter()
    fill_color = cc.e_value_to_color_rgba(e_value)
    stroke_pattern = goocanvas.LineDash([5.0, 10.0, 20.0, 10.0, 5.0])

    top_left = dict()
    top_right = dict()
    bottom_left = dict()
    bottom_right = dict()

    line_width = 0 # 0.35

    top_left['x'] = query_start/zoomFactor
    #top_left['y'] = height-6*line_width+((120*query)+50)
    top_left['y'] = height-6*line_width+((120*query)+50)-0.5
    top_right['x'] = query_end/zoomFactor
    top_right['y'] = height-6*line_width+((120*query)+50)-0.5
    bottom_left['x'] = subject_start/zoomFactor
    bottom_left['y'] = height+109+((120*query)+50)
    #bottom_left['y'] = ((120*query))+50-10
    bottom_right['x'] = subject_end/zoomFactor
    bottom_right['y'] = height+109+((120*query)+50)
    #bottom_right['y'] = ((120*query))+50-10


    #print top_left['x'],top_left['y'] 
    #print top_right['x'], top_right['y']
    #print bottom_left['x'], bottom_left['y']
    #print bottom_right['x'], bottom_right['y']

    points = goocanvas.Points([(top_left['x'],top_left['y']),(top_right['x'], top_right['y']),
                               (bottom_right['x'],bottom_right['y']),(bottom_left['x'], bottom_left['y'])])

    self.polylineModel = PolylineModelListener(parent=group,
                                            points=points,
                                            close_path=True,
                                            stroke_color=stroke_color,
                                            fill_color_rgba=fill_color,
                                            line_width=line_width)


    self.blastAlignmentLabel = BlastAlignmentLabel(parent=group, text='%s' % (e_value),
                               x=(top_right['x']+top_left['x']+bottom_left['x']+bottom_right['x'])/4.0,
                               y=(top_right['y']+top_left['y']+bottom_left['y']+bottom_right['y'])/4.0,
                               anchor=gtk.ANCHOR_CENTER,
                               font="Arial 8")

    self.polylineModel.set_data('type', 'blastAlignment')
    self.polylineModel.set_data('label', self.blastAlignmentLabel)





class BlastMatch:
  def __init__(self, params):
    #print params
    query, subject, percent_identity, alignment_length, mismatches, gap_openings, \
      q_start, q_end, s_start, s_end, e_value, bit_score = params
    self.properties = dict()
    self.properties['query'] = query
    self.properties['subject'] = subject
    self.properties['percent_identity'] = percent_identity
    self.properties['alignment_length'] = alignment_length
    self.properties['mismatches'] = mismatches
    self.properties['gap_openings'] = gap_openings
    self.properties['q_start'] = q_start
    self.properties['q_end'] = q_end
    self.properties['s_start'] = s_start
    self.properties['s_end'] = s_end
    self.properties['e_value'] = e_value
    self.properties['bit_score'] = bit_score

class BLAST2Seq:
  def __init__(self, c, query, subject, threshold=1e-4):
    print 'query: %s :: subject: %s' % (query, subject)
    self.c = c
    self.query = query
    self.subject = subject
    self.threshold = threshold
    self.query_file = os.path.join('/tmp', 'bl2seq.query')
    self.subject_file = os.path.join('/tmp', 'bl2seq.subject')
    self.results = os.path.join('/tmp', 'bl2seq.query_subject')
    self.textResults = os.path.join('/tmp', 'bl2seq.query_subject.txt')
    self.matches = []
    self.formatted_matches = []
    self.write_query()
    self.write_subject()
    self.bl2seq()

  def write_query(self):
    self.query_fasta = get_fasta_from_phage(self.c, self.query)
    out = open(self.query_file, 'w')
    out.write(self.query_fasta)
    out.close()

  def write_subject(self):
    self.subject_fasta = get_fasta_from_phage(self.c, self.subject)
    out = open(self.subject_file, 'w')
    out.write(self.subject_fasta)
    out.close()

  def bl2seq(self):
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    BLAST_dir = cfg.get('Phamerator','BLAST_dir')
    os.system('%s -p blastn -i %s -D 1 -F F -j %s -o %s' % (os.path.join(BLAST_dir, 'bin/' ,'bl2seq'), self.query_file, self.subject_file,  self.results))
    os.system('%s -p blastn -i %s -D 0 -F F -j %s -o %s' % (os.path.join(BLAST_dir, 'bin/' ,'bl2seq'), self.query_file, self.subject_file,  self.textResults))

  def get_results(self):
    results = open(self.results).readlines()
    for result in results:
      if not result.startswith('#'):
        self.matches.append(BlastMatch(result.split('\t')))
    for match in self.matches:
      if float(match.properties['e_value']) <= self.threshold:
        self.formatted_matches.append((int(match.properties['q_start']), int(match.properties['q_end']),
        int(match.properties['s_start']), int(match.properties['s_end']), float(match.properties['e_value'])),)
    return self.formatted_matches

class Phage:
  def __init__(self, c, PhageID):
    self.c = c
    self.PhageID = PhageID
  def _get_blast_matches(self, subject):
    bl2seq = BLAST2Seq(self.c,self.PhageID, subject)
    self.matches = bl2seq.get_results()
    return self.matches
class CanvasInterface:
  def __init__(self, c, canvas, phages=None, length=None):
    print 'init CanvasInterface'
    self.root = None
    self.c = c
    self.db = pham.db(c = self.c)
    self.canvas = canvas
    self.genes = []
    self.canvas.connect('item-created', self.on_item_created)
    #self.root = self.create_canvas_model(phages, length)
    #self.canvas.set_root_item_model(self.root)
    #self.canvas.connect("button_press_event", self.on_canvas_button_press)
    print 'root: %s' % self.root
    self.prefs = { 'defaultRectColor' : 'black', 'activeRectColor' : 'blue',
    'selectedRectColor' : 'orange', 'activeRectLineWidth' : 1.0, 'selectedRectLineWidth' : 2.0, 'defaultRectLineWidth' : 1.0}
    self.selectedCanvasItems = []
    self.dragging = False
    self.highlighted_text = None

    self.client = gconf.client_get_default()
    self.client.add_dir('/apps/phamerator', gconf.CLIENT_PRELOAD_NONE)
    print 'registering /apps/phamerator/gene_color'

  def create_canvas_model(self, phages=None, length=None):
    c = self.c
    self.phages = phages
    #if isinstance(self.root, goocanvas.GroupModel):
    #  print 'removing old root group', '&' * 155
    #  self.root.remove()
    self.root = goocanvas.GroupModel()
    self.blastMatches = []
    if not phages:
      item = goocanvas.TextModel(text="Select a genome from the main window",
                x=5, y=20,
                anchor=gtk.ANCHOR_WEST,
                font="Arial 12")
      print 'adding a blank phageGroup'
      self.root.add_child(item, -1)
      return self.root
      
      # calculate this here, not in the loop below
    largestPhams, self.largestPhamSize = get_largest_pham_size(self.c)
      
    for n, p in enumerate(phages):
      PhageID = p['PhageID']
      phageName = get_phage_name_from_PhageID(c, PhageID)
      phageGroup = phameratorGroupModel(parent = self.root)
      phageGroup.set_data('type', 'phageGroup')
      phageGroup.set_data('name', phageName)

      scaleVGroup = goocanvas.GroupModel( parent = phageGroup)
      scaleVGroup.set_data('type', 'scaleVGroup')

      geneGroup = goocanvas.GroupModel(parent = phageGroup)
      geneGroup.set_data('type', 'geneGroup')

      scaleHGroup = goocanvas.GroupModel(parent = phageGroup)
      scaleHGroup.set_data('type', 'scaleHGroup')


      phageGroup.set_data('scaleVGroup', scaleVGroup)
      phageGroup.set_data('scaleHGroup', scaleHGroup)
      phageGroup.set_data('geneGroup', geneGroup)

      display_reversed = p['display_reversed']
      print 'drawing phage:', PhageID, '-->', phageName
      height = 12 # height of gene boxes
      print n, PhageID

      #vert = 120*n+50
      vert = 0
      phageGroup.translate(0,120*n+50)

      print 'vert:', vert
      spacer = 13 # FIXME
      line_width = 0.5
      scale_height = 10.0

      item = goocanvas.TextModel(text=phageName,
                # x=5, y=vert-30,
                x=0, y=0,
                anchor=gtk.ANCHOR_WEST,
                font="Arial 12")
      item.set_data('type', 'phageName')
      item.translate(5, vert-30)
      phageGroup.add_child(item, -1)
      zoomFactor = 20.0
      self.root.set_data('zoomFactor', zoomFactor)
      genomeLength = get_length_of_genome(c, PhageID)    
 
      self.draw_scale(scaleHGroup, scaleVGroup, display_reversed=display_reversed, x=0, y=vert+(2*height)+(4*line_width), length=genomeLength, height=scale_height, line_width=line_width, zoomFactor=zoomFactor)

      phage = Phage(c, PhageID)


      GeneIDs = get_genes_from_PhageID(c, PhageID)
      genes = []
 
      for GeneID in GeneIDs:
        phage = get_phage_name_from_GeneID(c, GeneID)
        name = get_gene_name_from_GeneID(c, GeneID)
        exp = re.compile('(PBI)*[1-9]+\d*[.]*\d*$', re.IGNORECASE)
        try:
          name = exp.search(name).group().strip()
          #name = exp.split(name)[-1]
        except: print 'EXCEPTION: %s, %s' % (phage, name)
        start, stop, length, orientation = get_gene_start_stop_length_orientation_from_GeneID(c, GeneID)
        if display_reversed:
          if orientation == 'F': orientation = 'R'
          elif orientation == 'R': orientation = 'F'
          newstart = genomeLength - stop + 1
          stop  = genomeLength - start - 1
          start = newstart
        g = gene.gene(GeneID, name, start, stop, length, orientation)
        pham = get_pham_from_GeneID(c, GeneID)
        domains = get_domain_hits_from_GeneID(c, GeneID)
        genes.append((g, pham, domains))
        genes.sort()
 
      up = 0
      y = None
      cc = ColorConverter()
      for g, p, d in genes:
        gc = get_gene_percent_GC(self.c, g.GeneID)
        if gc != -1: gc_color = cc.GC_to_color(get_gene_percent_GC(self.c, g.GeneID))
        else: gc_color = '#ff0000'

        abundance = {}
        abundance = get_number_of_pham_members(self.c, p)
        abundance_color = cc.gene_abundance_to_color(abundance, self.largestPhamSize)
        
        cluster = get_cluster_from_PhageID(self.c, get_PhageID_from_GeneID(self.c, g.GeneID))
        if cluster:
          cluster = cluster[0] # ignore subclusters for now...
        intra_conservation = ""
        inter_conservation = ""
        if cluster:
          clusterPhageIDs = set(get_PhageIDs_from_cluster(self.c, cluster))
        else:
          clusterPhageIDs = set([get_PhageID_from_GeneID(self.c, g.GeneID)])
        phamPhageIDs = set(get_PhageID_members_of_pham(self.c, p))
        allPhageIDs = set(get_PhageIDs(self.c))
        print allPhageIDs, phamPhageIDs, clusterPhageIDs
        if allPhageIDs == phamPhageIDs:
          intra_conservation = 'all'
          inter_conservation = 'all'
        elif clusterPhageIDs == phamPhageIDs:
          intra_conservation = 'all'
          inter_conservation = None
        elif clusterPhageIDs < phamPhageIDs:
          intra_conservation = 'all'
          inter_conservation = 'some'
        elif phamPhageIDs < clusterPhageIDs:
          intra_conservation = 'some'
          inter_conservation = None
        elif (allPhageIDs - clusterPhageIDs) == (phamPhageIDs - clusterPhageIDs):
          intra_conservation = 'some'
          inter_conservation = 'all'
        else:
          intra_conservation = 'some'
          inter_conservation = 'some'

        print "intra: %s inter: %s" % (intra_conservation, inter_conservation)
        conservation_color = cc.gene_cluster_conservation_to_color(intra_conservation, inter_conservation)

        if g.orientation == 'F':
          #fillColor = 'green'
          if up: y = vert
          else: y = vert + height + 3*line_width
        else:
          #fillColor = 'red'
          if up: y = vert + height*2 + scale_height + line_width*5
          else:  y = vert + height*2 + scale_height + line_width*5 + height
        h=s=v=0
        numberOfMembers = get_number_of_pham_members(self.db.c, p)
        #print g.name, '->', numberOfMembers
        if numberOfMembers > 1:
          hsv = self.db.select('pham_color', 'color', name=p)
          rgb = hsv[0][0]
        else:
          rgb = '#ffffff'

        # if this gene wraps from the right end of the genome to the left end of the genome
        if g.start > g.stop and g.orientation == 'F':
          print 'wrap around gene: forward'
          start = g.start
          stop = genomeLength
          length = stop - start
          print 'name: %s, GeneID: %s, start: %s, stop: %s, length: %s' % (g.name, g.GeneID, start, stop, length)
          f1 = gene.gene(g.GeneID, g.name, start, genomeLength, length, orientation)
          gene_model = self.draw_gene(geneGroup, f1, p, y, zoomFactor, height, pham_color=rgb, gc_color=gc_color, abundance_color=abundance_color, cluster_conservation_color = conservation_color)
          self.genes.append(geneModel)
          start = 0
          stop = g.stop
          length = stop - start
          print 'start: %s, stop: %s, length: %s' % (start, stop, length)
          f2 = gene.gene(g.GeneID, g.name, start, g.stop, length, orientation)
          self.draw_gene(geneGroup, f2, p, y, zoomFactor, height, pham_color=rgb, gc_color=gc_color, abundance_color=abundance_color, cluster_conservation_color=conservation_color, domains=d)

          # self.draw_gene(self, t, y, zoomFactor, height):

        # else if this gene wraps from the left end of the genome to the right end of the genome
        elif g.start > g.stop and g.orientation == 'R':
          print 'wrap around gene: reverse (but it is not being drawn)'
          pass
        # a typical gene
        else:
          gene_model = self.draw_gene(geneGroup, g, p, y, zoomFactor, height, pham_color=rgb, gc_color=gc_color, abundance_color=abundance_color, cluster_conservation_color=conservation_color, domains=d)
          self.genes.append(gene_model)
          while gtk.events_pending():
            gtk.main_iteration(False)
        if up: up = False
        else: up = True
    import ConfigParser
    cfg = ConfigParser.RawConfigParser()
    cfg.read(os.path.join(os.environ['HOME'], '.phamerator', 'phamerator.conf'))
    if cfg.get('Phamerator','draw_blast_alignments') == 'True':
      self.draw_blastn_alignments()
    return self.root

  def draw_blastn_alignments(self):
    print 'draw_blastn_alignments()'
    group = phameratorGroupModel()
    group.props.stroke_color = 'black'
    group.props.line_width = 1

    phages = self.phages
    for n, p in enumerate(phages):
      #print 'drawing blast alignment'
      PhageID = p['PhageID']
      phageName = get_phage_name_from_PhageID(self.c, PhageID)
      g = self.root.get_n_children()
      for i in range(0, g):
        child = self.root.get_child(i)
        if child.get_data('name') == get_phage_name_from_PhageID(self.c, PhageID):
          phageGroup = child
          query_offset = phageGroup.get_simple_transform()[0]
          break
      scaleVGroup = phageGroup.get_data('scaleVGroup')

      display_reversed = p['display_reversed']

      vert = 0

      spacer = 13 # FIXME
      line_width = 0 # 0.35
      scale_height = 10.0
      zoomFactor = 20.0
      genomeLength = get_length_of_genome(self.c, PhageID)    
 
      phage = Phage(self.c, PhageID)
      try:
        subject = self.phages[n+1]['PhageID']
      except:
        subject = None

      if subject:

        g = self.root.get_n_children()
        for i in range(0, g):
          child = self.root.get_child(i)
          if child.get_data('name') == get_phage_name_from_PhageID(self.c, subject):
            subjectPhageGroup = child
            subject_offset = subjectPhageGroup.get_simple_transform()[0]
            break

        for match in phage._get_blast_matches(subject=subject):
          if display_reversed:
            blastMatch = BlastAlignmentModel(group=group,
             query=n,
             query_start=genomeLength-match[0],
             query_end=genomeLength-match[1],
             subject=None,
             subject_start=match[2],
             subject_end=match[3],
             e_value=match[4],
             zoomFactor=20.0,
             height=vert+(0)+(4*line_width))
          else:
            blastMatch = BlastAlignmentModel(group=group,
                                     query=n,
                                     query_start=match[0]+query_offset*zoomFactor,
                                     query_end=match[1]+query_offset*zoomFactor,
                                     subject=None,
                                     subject_start=match[2]+subject_offset*zoomFactor,
                                     subject_end=match[3]+subject_offset*zoomFactor,
                                           e_value=match[4],
                                     zoomFactor=20.0,
                                     #height=vert+(35)+(4*line_width))
                                     height= 50 - spacer)
          self.blastMatches.append(blastMatch)  
    self.root.add_child(group, 0)
    # move this code to on_polyline_enter/leave
    #try:
    #  group.raise_(above=subjectPhageGroup)
    #except:
    #  pass
  # from pygoocanvas demo.py
  def create_stipple (self, color_name, stipple_data):
    import cairo
    color = gtk.gdk.color_parse (color_name)
    stipple_data[2] = stipple_data[14] = color.red >> 8
    stipple_data[1] = stipple_data[13] = color.green >> 8
    stipple_data[0] = stipple_data[12] = color.blue >> 8
    surface = cairo.ImageSurface.create_for_data (stipple_data, cairo.FORMAT_ARGB32, 2, 2, 8)
    pattern = cairo.SurfacePattern(surface)
    pattern.set_extend (cairo.EXTEND_REPEAT)

    return pattern

  def draw_gene(self, group, g, p, y, zoomFactor, height, pham_color, gc_color, abundance_color, cluster_conservation_color, domains=[]):
    cc = ColorConverter()
    color_by = self.client.get_string('/apps/phamerator/gene_color')
    color_dict = {'color_by_abundance': abundance_color, 'color_by_cluster_conservation': cluster_conservation_color, 'color_by_phamily': pham_color, 'color_by_gc': gc_color, 'no_color': 'white'}

    if not color_dict.has_key(color_by):
      color_by = 'color_by_phamily'
      self.controller.mapWTree.get_object(color_by).set_active(True)
      self.client.set_string('/apps/phamerator/gene_color', 'color_by_phamily')
    rectModel = geneModel(x=0, y=0, width=float(g.length/zoomFactor), height=height,
		  line_width=1.0,
		  radius_x=1.0,
		  radius_y=1.0,
		  fill_color=color_dict[color_by])

    rectModel.set_data("name", g.name)
    rectModel.set_data("GeneID", g.GeneID)
    rectModel.set_data('type', 'gene')
    rectModel.set_data("status", 'default')
    rectModel.set_data('pham', p)
    rectModel.set_data("phamily_color", pham_color)
    rectModel.set_data("gc_color", gc_color)
    rectModel.set_data("abundance_color", abundance_color)
    rectModel.set_data("cluster_conservation_color", cluster_conservation_color)
    group.add_child(rectModel, -1)
    rectModel.translate(g.start/zoomFactor,y)

    for n, domain in enumerate(domains):
      domainGroupModel = goocanvas.GroupModel()
      group.add_child(domainGroupModel, -1)
      # domain coordinates are in amino acids, so multiply by 3 for DNA positions
      if g.orientation == 'F':
        start, end, e_value, description = domain['start'] * 3, domain['end'] * 3, domain['expect'], domain['description']
      elif g.orientation == 'R':
        end, start, e_value, description = domain['start'] * 3, domain['end'] * 3, domain['expect'], domain['description']
      else:
        print 'domain error!'
        sys.exit()
      domain_length = abs(start - end)
      domain_height=(height-1.0)/float(len(domains))
      domain_model = domainModel(x=0, y=n*domain_height+0.5, width=float(domain_length/zoomFactor), height=domain_height,
        line_width=0.3,
        radius_x=0.2,
        radius_y=0.2,
        fill_color_rgba =  0xFFDB1Cff) #cc.e_value_to_color(e_value))
      domain_model.set_data('type', 'domainModel')
      domain_model.set_data('domain', domain)
      domainGroupModel.add_child(domain_model, -1)

      if g.orientation == 'F':
        domain_model.translate((g.start+start)/zoomFactor,y)
      if g.orientation == 'R':
        domain_model.translate(((g.start+g.length)-start)/zoomFactor,y)
      domain_model.set_data('domainGroupModel', domainGroupModel)

    item = goocanvas.TextModel(text=g.name,
      #x=float((g.start+g.start+g.length)/2.0)/zoomFactor, y=y+height/2.0,
      x=0, y=0,
      anchor=gtk.ANCHOR_CENTER,
      font="Arial 4")
    item.set_data('type', 'gene')
    item.set_data('text', g.name)
    group.add_child(item, -1)
    item.translate(float((g.start+g.start+g.length)/2.0)/zoomFactor, y+height/2.0)

    if g.orientation == 'F':
      py = y - height/2.0
    else:
      py = y + height*1.5
    # pham label
    if p:
      if g.orientation == 'F':
        phamAnchor = gtk.ANCHOR_WEST
      else:
        phamAnchor = gtk.ANCHOR_EAST

      translation_length = len(get_translation_from_GeneID(self.db.c, g.GeneID))
      if translation_length >= 120:
        phamAnchor = gtk.ANCHOR_CENTER

      numberOfMembers = get_number_of_pham_members(self.db.c, p)

      px = float((g.start+g.start+g.length)/2.0)/zoomFactor
      # item should be a TextModelListener
      #item = goocanvas.TextModel(text='%s (%s)' % (p, numberOfMembers),
      item = PhamNameLabel(text='%s (%s)' % (p, numberOfMembers),
        # x=px, y=py,
        x=0, y=0,
        anchor=phamAnchor,
        font="Arial 4")
      item.set_data('type', 'pham')
      item.set_data('text', p)
      if translation_length < 120:
        #print 'rotating label for pham', p, "(270, %s, %s)" % (px,py)
        item.rotate(270,px, py)
      else:
        item.rotate(270,px, py)
        #item.translate(0,0)
      if translation_length >= 120:
        #item.rotate(89,px, py)
        item.rotate(90,px, py)
      group.add_child(item, -1)
      item.translate(px,py)

      # if the gene has a description, show it
      desc = get_description_from_GeneID(self.db.c, g.GeneID)
      #print desc
      if desc:
        descModel = GeneDescriptionLabel(text=desc,
                                        # x=float((g.start+g.start+g.length)/2.0)/zoomFactor,
                                        x=0,
                                        # y=y-40,
                                        y=0,
                                        anchor=gtk.ANCHOR_CENTER,
                                        font='Arial 4',
                                        ellipsize=pango.ELLIPSIZE_END,
                                        width=g.length/zoomFactor)
        descModel.set_data('type', 'desc')
        group.add_child(descModel, -1)
        descModel.translate(float((g.start+g.start+g.length)/2.0)/zoomFactor, y-40)
    return rectModel

  def draw_scale(self, scaleHGroup, scaleVGroup, display_reversed, x, y, height, length, line_width=0.5, zoomFactor=1):
    '''draws the scale bar on a linear genome map'''
    c = self.c
   
    #print 'drawing scale at (%s,%s)' % (x,y)
    #print 'length:', length
    trueLength = length
    length = length / float(zoomFactor)
    #pos = 0
    small = 100
    top = 500
    large = 1000
    topLine = (x, y)
    bottomLine = (x, y+height)
    for line in (topLine, bottomLine):
      #rect_model = goocanvas.RectModel(x=float(line[0]), y=line[1], width=length, height=line_width,
      rect_model = goocanvas.RectModel(x=0, y=0, width=length, height=line_width,
      line_width=line_width,
      radius_x=0,
      radius_y=0,
      fill_color="#000000")
      rect_model.set_data('type', 'scale')
      scaleHGroup.add_child(rect_model, -1)
      rect_model.translate(float(line[0]), line[1])
    basePositions = range(int(x), int(x+trueLength+1))
    if display_reversed: basePositions.reverse()
    for i in basePositions:
      if (not display_reversed and not i % large) or (display_reversed and not (trueLength-i) % large):
        # draw large scale bar
        #rect_model = goocanvas.RectModel(x=float(i)/zoomFactor, y=y, width=line_width, height=height-line_width,
        rect_model = goocanvas.RectModel(x=0, y=0, width=line_width, height=height-line_width,
        line_width=line_width,
        radius_x=0,
        radius_y=0,
        fill_color="#000000")
        #print i
        rect_model.set_data('type', 'scale')
        scaleVGroup.add_child(rect_model, -1)
        rect_model.translate(float(i)/zoomFactor, y)
        if display_reversed:
          label_model = goocanvas.TextModel(text=str(int(i/1000)),
                  #x=(trueLength-float(i)+500)/zoomFactor, y = (( y + (y+height))/2 + y)/2,
                  x=0, y=0,
                  anchor=gtk.ANCHOR_EAST,
                  font="Arial 3",
                  fill_color="#009900")
          label_model.translate((trueLength-float(i)+500)/zoomFactor, (( y + (y+height))/2 + y)/2)

        else:
          label_model = goocanvas.TextModel(text=str(int(i/1000)),
                  # x=(float(i)+50)/zoomFactor, y = (( y + (y+height))/2 + y)/2,
                  x=0, y=0,
                  anchor=gtk.ANCHOR_WEST,
                  font="Arial 3",
                  fill_color="#009900")
        label_model.set_data('type', 'marker')
        label_model.set_data('text', str(int(i/1000)))
        label_model.set_data('type', 'scale')
        scaleVGroup.add_child(label_model, -1)
        label_model.translate((float(i)+50)/zoomFactor, (( y + (y+height))/2 + y)/2)
      #elif not i % top:
      elif (not display_reversed and not i % top) or (display_reversed and not (trueLength - i) % top):
        # draw top scale bar
        # rect_model = goocanvas.RectModel(x=float(i)/zoomFactor, y=y, width=line_width, height=height/2,
        rect_model = goocanvas.RectModel(x=0, y=0, width=line_width, height=height/2,
        line_width=line_width,
        radius_x=0,
        radius_y=0,
        fill_color="#000000")
        rect_model.set_data('type', 'scale')
        scaleVGroup.add_child(rect_model, -1)
        rect_model.translate(float(i)/zoomFactor, y)

      #elif not i % small:
      elif (not display_reversed and not i % small) or (display_reversed and not (trueLength - i) % small):

        # draw small scale bar
        #rect_model = goocanvas.RectModel(x=float(i)/zoomFactor, y=y+(height-height/2), width=line_width, height=height/2,
        rect_model = goocanvas.RectModel(x=0, y=0, width=line_width, height=height/2,
        line_width=line_width,
        radius_x=0,
        radius_y=0,
        fill_color="#000000")
        rect_model.set_data('type', 'scale')
        scaleVGroup.add_child(rect_model, -1)
        rect_model.translate(float(i)/zoomFactor, y+(height-height/2))

  ## This is our handler for the "item-created" signal of the GooCanvasView.
  def on_item_created (self, canvas, item, model):
    #print "item created :: canvas: %s, item: %s, model: %s, " % (canvas, item, model)
    if isinstance(item, goocanvas.Text):
      item.connect("button-press-event", self.on_text_button_press)
      item.connect("button-release-event", self.on_text_button_release)
      item.connect("enter-notify-event", self.on_text_enter)
      item.connect("leave-notify-event", self.on_text_leave)
      item.connect("motion-notify-event", self.on_motion_notify)
      if item.get_model().get_data('type') == 'domainLabelModel':
        b= item.get_bounds()
        item.get_model().set_data('x', b.x1)
        item.get_model().set_data('y', b.y1)
        item.get_model().set_data('width', b.x2 - b.x1)
        item.get_model().set_data('height', b.y2 - b.y1)
        print 'adding domain label...'
        item.get_model().set_data('domainLabel', item)
    if isinstance(item, goocanvas.Rect):
      item.connect("button-press-event", self.on_rect_button_press)
      item.connect("button-release-event", self.on_rect_button_release)
      item.connect("enter-notify-event", self.on_rect_enter)
      item.connect("leave-notify-event", self.on_rect_leave)
      item.connect("motion-notify-event", self.on_motion_notify)
    if isinstance(item, goocanvas.Polyline):
      item.connect("enter-notify-event", self.on_polyline_enter)
      item.connect("leave-notify-event", self.on_polyline_leave)
    if isinstance(item, goocanvas.Group):
      item.connect("button-press-event", self.on_group_button_press)
      item.connect("motion-notify-event", self.on_group_motion_notify)
      item.connect("button-release-event", self.on_group_button_release)

  def on_polyline_button_press(self, view, target, event):
    print 'polyline clicked'
    view.lower(None)

  def on_group_button_press(self, view, target, event):
    #print 'group clicked'
    print view
    if view.get_model() != self.canvas.get_root_item_model():
      return True
    selectionRect = self.canvas.get_root_item_model().get_data('selectionRect')
    if selectionRect:
      selectionRect.remove()
    #if (event.state & gtk.gdk.BUTTON1_MASK and not event.state & gtk.gdk.CONTROL_MASK):
    #  return True
    bounds = self.canvas.get_bounds()
    rectModel = goocanvas.RectModel(parent=self.canvas.get_root_item_model(),
                x=event.x,
                y=0,
                width=0,
                line_width=0.6,
                height=bounds[3]-bounds[1],
                #fill_color_rgba=0x0000ff44)
                fill_color_rgba=0x00ff0044)
    #rectModel.translate(event.x, 0)
    self.canvas.get_root_item_model().set_data('selectionRect', rectModel)
    rectModel.set_data('resizing', True)

  def on_group_motion_notify(self, view, target, event):
    if view.get_model() != self.canvas.get_root_item_model():
      return True
    selectionRect = self.canvas.get_root_item_model().get_data('selectionRect')
    if not selectionRect:
      return True
    if not selectionRect.get_data('resizing'):
      return True    
    if event.x > selectionRect.props.x:
      selectionRect.props.width = event.x - selectionRect.props.x
    return True

  def on_group_button_release(self, view, target, event):
    if view.get_model() != self.canvas.get_root_item_model():
      return True

    selectionRect = self.canvas.get_root_item_model().get_data('selectionRect')
    if selectionRect.props.x == event.x:
      selectionRect.remove()
      self.show_fasta_sequences(None)
      return True

    if not selectionRect:
      return True

    selectionRect.set_data('resizing', False)
    fasta = self.get_fasta_from_selectionRect(selectionRect)
    self.show_fasta_sequences(fasta)
    return False

  def on_polyline_enter(self, view, target, event):
    itemModel = view.get_model()
    if itemModel.get_data('type') == 'blastAlignment':
      if self.client.get_bool('/apps/phamerator/show_alignment_text') == False:
        itemModel.get_data('label').props.visibility = goocanvas.ITEM_VISIBLE

  def on_polyline_leave(self, view, target, event): 
    itemModel = view.get_model()
    if itemModel.get_data('type') == 'blastAlignment':
      if self.client.get_bool('/apps/phamerator/show_alignment_text') == False:
        itemModel.get_data('label').props.visibility = goocanvas.ITEM_INVISIBLE

  def on_text_button_press(self, view, target, event):
    '''display information about the selected text'''
    print view.get_data('type')
    if event.state & gtk.gdk.CONTROL_MASK:
      if view.get_model().get_data('type') == 'phageName': 
        cursor = gtk.gdk.Cursor (gtk.gdk.SB_H_DOUBLE_ARROW)
        for blastMatch in self.blastMatches:
          blastMatch.blastAlignmentLabel.remove()
          blastMatch.polylineModel.remove()
    else:
      if view.get_model().get_data('type') == 'pham':
        print 'you clicked on pham', view.get_model().get_data('text')
        cursor = gtk.gdk.Cursor (gtk.gdk.LEFT_PTR)
      elif view.get_model().get_data('type') == 'phageName': 
        cursor = gtk.gdk.Cursor (gtk.gdk.SB_V_DOUBLE_ARROW)
        for blastMatch in self.blastMatches:
          blastMatch.blastAlignmentLabel.remove()
          blastMatch.polylineModel.remove()
        # get current position of phageGroups
        print 'you clicked on phageName'
        item = view
        while item.get_model().get_data('type') != 'phageGroup':
          item = item.get_parent()
        print 'got phageGroup!'
      else:
        print view.get_model().props.text
    self.canvas.pointer_grab (view, gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK, cursor, event.time)
    return False

  def on_text_button_release(self, view, target, event):
    self.canvas.pointer_ungrab (view, event.time)
    # only redraw blastn alignments if user released click on phage name
    if view.get_model().get_data('type') != 'phageName':
      #self.draw_blastn_alignments()
      return
    # get current position of phageGroups
    n = self.canvas.get_root_item_model().get_n_children()
    phages = {}
    for child in range(0, n):
      group = self.canvas.get_root_item_model().get_child(child)
      if group.get_data('type') == 'phageGroup':
        phages[group.y] = group
    keys = phages.keys()
    keys.sort()
    count = 0
    for key in keys:
      print phages[key].get_data('name'), phages[key].y
      phages[key].translate(0, (120*count+50)-key)
      x = phages[key].get_simple_transform()[0]
      if x < 0:
        phages[key].translate(-x, 0)
      count = count + 1

    new_phages = []
    for key in keys:
      for d in self.phages:
        name = get_PhageID_from_name(self.c, phages[key].get_data('name'))
        print 'name: %s' % name
        if d['PhageID'] == name:
          new_phages.append(d)

    self.phages = new_phages
    print self.phages
    self.draw_blastn_alignments()
    # for key in key, translate phages[key] if needed to put it back in the proper spacing.

  def on_text_enter(self, view, target_view, event):
    itemModel = view.get_model()
    if itemModel.get_data('type') == 'desc':
      try:
        self.selected_text.remove()
        backRect = itemModel.get_data('backRect')
        backRect.remove()
      except:
        pass
      #itemModel.props.ellipsize = pango.ELLIPSIZE_NONE

  def on_text_leave(self, view, target_view, event):
    itemModel = view.get_model()
    if itemModel.get_data('type') == 'desc':
      pass
      #backRect = itemModel.get_data('backRect')
      #backRect.props.visibility = False
      #backRect.remove()
      #itemModel.props.ellipsize = pango.ELLIPSIZE_END

  def color_by_has_changed(self, client, *args, **kwargs):
    print 'color_by_has_changed'
    pass

  def on_motion_notify (self, item, target, event):
    '''called when mouse moves over canvas items, it handles the dragging of canvas items'''
    if event.state & gtk.gdk.BUTTON1_MASK and item.get_model().get_data('type') == 'phageName':
      while item.get_model().get_data('type') != 'phageGroup':
        item = item.get_parent()
      if not (event.state & gtk.gdk.CONTROL_MASK):
        item.get_model().translate(0, event.y)
      elif (event.state & gtk.gdk.CONTROL_MASK):
        item.get_model().translate(event.x, 0)
        phageGroup = item
        #start_x = phageGroup.get_bounds().x1
        #new_x = event.x
        #new_y = event.y
        pBounds = phageGroup.get_bounds()
        rBounds = self.canvas.get_root_item().get_bounds()
        px1, py1, px2, py2 = pBounds.x1, pBounds.y1, pBounds.x2, pBounds.y2
        rx1, ry1, rx2, ry2 = rBounds.x1, rBounds.y1, rBounds.x2, rBounds.y2
        
        upper = max(px2, rx2)

        #sw = self.controller.mapWTree.get_object('MapWindowScrolledWindow')
        #self.canvas.set_bounds(px1, py1, upper, py2)
        scale = self.canvas.get_scale()
        self.canvas.set_size_request(int((upper+10)*scale), int((ry2-ry1+20)*scale))
        #hAdj = sw.get_hadjustment()
        #hAdj.upper = rx2
        #print 'page_size: %s' % hAdj.page_size 
        #print 'upper: %s' % upper
        #hAdj.changed()
        #self.dragging == False
        return False

  def on_rect_button_press (self, item, target_item, event):
    r = item
    #print 'status before clicking: %s' % r.get_model().get_data('status')
    #print 'item: %s target_item: %s event: %s event.type: %s event.state: %s' % (item, target_item, event, event.type, event.state)

    if event.button == 3:
      for g in self.genes:
        g.change_color(self.client)
        print g.get_data('pham')
        if g.get_data('pham') != r.get_model().get_data('pham'):
          g.props.fill_color = '#eeeeee'

    if item.get_model().get_data('type') == 'gene':
      print 'setting gene to active'
      # unselect this gene
      if r.get_model().get_data('status') == 'selected':
        if event.state & gtk.gdk.CONTROL_MASK:
          r.get_model().set_data('status', 'default')
          r.get_model().props.stroke_color = self.prefs['activeRectColor']
          r.get_model().props.line_width = self.prefs['activeRectLineWidth']
          self.selectedCanvasItems.remove(r)
        else:
          r.get_model().set_data('status', 'default')
          r.get_model().props.stroke_color = self.prefs['activeRectColor']
          r.get_model().props.line_width = self.prefs['activeRectLineWidth']
          self.controller.DNATextBuffer.set_text('click on a gene')
          self.controller.ProteinTextBuffer.set_text('click on a gene')
          self.selectedCanvasItems = []

      elif r.get_model().get_data('status') == 'default':
        if event.state & gtk.gdk.CONTROL_MASK:
          # control key pressed, so add this gene to current selection
          r.get_model().set_data('status', 'selected')
          r.get_model().props.stroke_color = self.prefs['selectedRectColor']
          r.get_model().props.line_width = self.prefs['selectedRectLineWidth']
          self.selectedCanvasItems.append(r)
        else:
          # control key not pressed, so unselect everything and then select the clicked gene
          print 'setting gene to selected'
          # unselect the previously selected gene, if there is one
          for s in self.selectedCanvasItems:
            s.get_model().set_data('status', 'default')
            s.get_model().props.stroke_color = self.prefs['defaultRectColor']
            s.get_model().props.line_width = self.prefs['defaultRectLineWidth']
          self.selectedCanvasItems = []
          # select the gene that was just clicked
          r.get_model().set_data('status', 'selected')
          r.get_model().props.stroke_color = self.prefs['selectedRectColor']
          r.get_model().props.line_width = self.prefs['selectedRectLineWidth']
          self.selectedCanvasItems.append(r)
      self.controller.gene_selection_changed(self.selectedCanvasItems)


    elif item.get_model().get_data('type') == 'scale':
      group = item.get_parent()
      item.set_data('scaleBounds', group.get_bounds())
    print 'scale button press'
    self.drag_x = event.x
    self.drag_y = event.y

    return False

  def on_rect_button_release(self, item, target_item, event):
    print 'rect button release'
    self.canvas = item.get_canvas ()
    self.dragging = False
    #parent = item.get_parent()
    #n_children = parent.get_n_children()
    # return True
    return False
    
  def get_fasta_from_selectionRect(self, selectionRect):
    zoomFactor = self.root.get_data('zoomFactor')
    if not zoomFactor: return
    print 'zoomFactor: %s' % zoomFactor

    w = int(selectionRect.props.width * zoomFactor)
    fasta = ""

    for n, phage in enumerate(self.phages):
      #print 'drawing blast alignment'
      PhageID = phage['PhageID']
      print phage
      phageName = get_phage_name_from_PhageID(self.c, PhageID)
      g = self.root.get_n_children()
      for i in range(0, g):
        child = self.root.get_child(i)
        if child.get_data('name') == get_phage_name_from_PhageID(self.c, PhageID):
          phageGroup = child
          x = int((selectionRect.props.x - phageGroup.get_simple_transform()[0]) * zoomFactor)
          if x+w <= 0 or x >= phage['length']:
            continue
          start = max(x, 0)
          end = min(x+w, phage['length'])
          if start == x:
            fasta = fasta + '>' + get_phage_name_from_PhageID(self.c, phage['PhageID']) + \
            '_(' + str(x+1) + '-' + str(end) + ')\n' + \
            get_seq_from_PhageID(self.c, phage['PhageID'])[x:x+w] + '\n'
          else:
            fasta = fasta + '>' + get_phage_name_from_PhageID(self.c, phage['PhageID']) + \
            '_(' + str(start+1) + '-' + str(end) + ')\n' + \
            get_seq_from_PhageID(self.c, phage['PhageID'])[start:x+w] + '\n'
    return fasta

    #for phage in self.phages:
    #  fasta = fasta + '>' + get_phage_name_from_PhageID(self.c, phage['PhageID']) + \
    #  '_[' + str(x) + ', ' + str(x+w) + ']\n' + \
    #  get_seq_from_PhageID(self.c, phage['PhageID'])[x:x+w] + '\n'
    #return fasta

  def show_gene_sequences(self, GeneIDs):
    DNASeq = ''
    proteinSeq = ''
    for GeneID in GeneIDs:
      DNASeq = DNASeq + '>' + GeneID + '\n' + get_seq_from_GeneID(self.c, GeneID) + '\n'
      proteinSeq = proteinSeq + '>' + GeneID + '\n' + get_translation_from_GeneID(self.c, GeneID) + '\n'
    controller = self.controller
    controller.DNATextBuffer.set_text(DNASeq)
    controller.ProteinTextBuffer.set_text(proteinSeq)
  
  def remove_ellipse(self, ellipse):
    ellipse.remove()
    return True
    
  def show_fasta_sequences(self, fasta):
    controller = self.controller
    if fasta:
      controller.DNATextBuffer.set_text(fasta)
    else:
      controller.DNATextBuffer.set_text('')
    controller.ProteinTextBuffer.set_text('')

  def on_rect_enter(self, item, target_item, event):
    if item.get_model().get_data('type') == 'scale':
      return
    r = item

    def add_tooltip(group, labelModel, r, x, y, width, height):
      print 'adding tooltip...'
      padding = 5.0
      tooltipBox = goocanvas.RectModel(x=x-(padding/2), y=y-(padding/2), width=width+padding, height=height+padding,
                   line_width=1,
                   radius_x=2.5,
                   radius_y=2.5,
                   stroke_color = 'black',
                   fill_color_rgba=0xD5FF8EDD)

      r.get_model().set_data('tooltip', tooltipBox)
      #group.get_model().add_child(tooltipBox, -1)
      self.canvas.get_root_item_model().add_child(tooltipBox, -1)

      tooltipBox.lower(below=labelModel)
      print 'done!'
      return False

    highlight = self.client.get_bool('/apps/phamerator/hover_highlights_pham')

    if highlight and r.get_model().get_data('type') == 'gene' and self.dragging == False:
      for g in self.genes:
        # for each gene, if it's not in the hovered pham, set it's fill color to gray
        if g.get_data('pham') != r.get_model().get_data('pham'):
          g.props.fill_color = '#eeeeee'
        else:
          # zap it with a laser!
          from_x = r.get_transform()[4] + r.get_model().get_parent().get_parent().get_transform()[4]
          from_x = from_x + (r.get_model().props.width/2.0)
          from_y = r.get_transform()[5] + r.get_model().get_parent().get_parent().get_transform()[5]
          from_y = from_y + (r.get_model().props.height/2.0)

          try:
            phageGroupMatrix = g.get_parent().get_parent().get_transform()
            to_x = (((g.get_transform()[4] + phageGroupMatrix[4] - from_x) * 2) + g.props.width) / 2.0
            to_y = (((g.get_transform()[5] + phageGroupMatrix[5] - from_y) * 2) + g.props.height) / 2.0
  
            ellipse_model = goocanvas.EllipseModel(parent = self.canvas.get_root_item_model(), center_x=from_x, center_y=from_y, radius_x=(g.props.width/2.0)+2, radius_y=(g.props.width/2.0)+2,
                                                   stroke_color='black', fill_color_rgba =  0xFABD0577,
                                                   line_width=0.75)
  
            ellipse_model.animate(to_x, to_y, 1, 0, True, 2000, 40, goocanvas.ANIMATE_FREEZE)
            gobject.timeout_add(15000, self.remove_ellipse, ellipse_model)
          except:
            print 'g is a: %s' % g.get_data('type')

      #group = r.get_parent()
      r.get_model().props.stroke_color = self.prefs['activeRectColor']
      r.get_model().props.line_width = self.prefs['activeRectLineWidth']
      return True

    if r.get_model().get_data('type') == 'domainModel':
      domainGroupModel = item.get_model().get_data('domainGroupModel')
      domain = item.get_model().get_data('domain')
      start, end, e_value, description = domain['start'] * 3, domain['end'] * 3, domain['expect'], domain['description']
  
      domainLabelModel = item.get_model().get_data('domainLabelModel')
      if domainLabelModel: domainLabelModel.remove()
      size = "Arial %s" % str(round(10.0*(1/self.canvas.get_scale())))
      width = 400.0/self.canvas.get_scale()
      domainLabelModel = goocanvas.TextModel(text=domain['description'],
        x=0, y=0,
        width = width,
        anchor=gtk.ANCHOR_NORTH_WEST,
        font=size)
      item.get_model().set_data('domainLabelModel', domainLabelModel)
      domainLabelModel.set_data('type', 'domainLabelModel')

      self.canvas.get_root_item_model().add_child(domainLabelModel, -1)
      domainLabelModel.set_transform(item.get_model().get_transform())

      zoomFactor = self.root.get_data('zoomFactor')
      if not zoomFactor: zoomFactor = 20.0
      phageGroup = item.get_parent().get_parent().get_parent()
      domainLabelModel.translate((phageGroup.get_model().get_simple_transform()[0]+(abs(end-start)+200)/zoomFactor), phageGroup.get_model().get_simple_transform()[1])

      if domainLabelModel:
        #domainLabelModel.translate(0, item.get_model().get_parent().get_simple_transform()[1])
        label = domainLabelModel.get_data('domainLabel')
        b = label.get_bounds()
        t = label.get_simple_transform()
        y = t[1]
        x = b.x1
        width = b.x2-b.x1
        height = b.y2-b.y1
        group = r.get_parent()
        add_tooltip(group, domainLabelModel, r, x, y, width, height)
      
      return True

  def on_rect_leave(self, item, target_item, event):
    domainLabelModel = item.get_model().get_data('domainLabelModel')
    if domainLabelModel: domainLabelModel.remove()
    itemModel = item.get_model()

    r = item
    if r.get_data('tooltip'): r.get_data('tooltip').remove()
    if r.get_model().get_data('type') == 'gene':
      for g in self.genes:
        g.change_color(self.client)
      if r.get_model().get_data('status') == 'default':
        r.get_model().props.stroke_color = self.prefs['defaultRectColor']
        r.get_model().props.line_width = self.prefs['defaultRectLineWidth']
      elif r.get_model().get_data('status') == 'selected':
        r.get_model().props.stroke_color = self.prefs['selectedRectColor']
        r.get_model().props.line_width = self.prefs['selectedRectLineWidth']

    if r.get_model().get_data('type') == 'domainModel':
      #tt = r.get_model().get_data('tooltip')
      r.get_model().get_data('domainLabelModel').remove()
      tt = r.get_model().get_data('tooltip')
      if tt: tt.remove()
    return True
 
  ## This is our handler for the "delete-event" signal of the window, which
  ##   is emitted when the 'x' close button is clicked. We just exit here. */
  def on_delete_event(self, window, event):
    raise SystemExit

if __name__ == "__main__":
  main(sys.argv)
