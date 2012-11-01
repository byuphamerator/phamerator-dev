try:
  import SOAPpy,cartographer, PhamDisplay,phamerator_manage_db,db_conf,goocanvas,tempfile,cairo,os,random,PhamDisplay,pham
except:
  import sys,os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
  import SOAPpy,cartographer,PhamDisplay,phamerator_manage_db,db_conf,goocanvas,tempfile,cairo,random,PhamDisplay,pham
import threading
class phageSOAP:
  
  def __init__(self):
    self.username = "anonymous"
    self.password = "anonymous"
    self.server = "localhost"
    self.database = "SEA"
    #dont forget to delete this folder on database update/change!
    self.cachedir = '/tmp/phageSOAP/cache/'
    try:
      os.mkdir('/tmp/phageSOAP')
      os.mkdir(self.cachedir)
    except:
      print '\n>Using existing cache directory.'
  def create_genome_map(self,phages):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    lengths = []
    for phage in phages:
      length = phamerator_manage_db.get_length_of_genome(self.c,phage["PhageID"])
      lengths.append(length)
    length = max(lengths)  
    self.canvas = goocanvas.Canvas()
    canvasInterface = cartographer.CanvasInterface(self.c, self.canvas)
    self.canvas.set_root_item_model(canvasInterface.create_canvas_model(phages, length))
    zoomFactor = 20.0
    self.canvas.set_bounds(0,0,length/zoomFactor, 100000)
    needs_new = True
    while needs_new == True:
      name = "/tmp/phageSOAP/tmp" + str(hash(str(random.randint(1,64563))+str(hash(self.canvas))))
      if os.path.exists(name):
        needs_new = True
      else:
        needs_new = False
    self.current_genome_map = name
    surface = cairo.SVGSurface (self.current_genome_map, (length/zoomFactor)+72, 5*72*len(phages))
    cr = cairo.Context (surface)
    cr.translate (36, 130)
    self.canvas.render (cr, None, 0.1)
    cr.show_page ()
    print "\n>genome map generated\n"
    return "genome map generated\n"
    
  def get_genome_map(self):
    
    myFile = open(self.current_genome_map)
    string = myFile.read()
    myFile.close()
    print "\n>genome map sent\n"
    return string

  def create_pham_circle(self,phamName,alignmentColor,adjustment,radius):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    filename = str(phamName) + str(alignmentColor) + str(adjustment) + str(radius)
    filelist = os.listdir(self.cachedir)
    for item in filelist:
      if item == filename:
        self.current_phamCircle = self.cachedir + filename
        string = "phamCircle " + str(phamName) + " found in cache, using cached version\n"
        print ">" + string
        return string
    self.radius = radius
    self.alignmentColor = alignmentColor
    self.threshold = 0.70
    self.phamCircleCanvas = goocanvas.Canvas()
    GeneIDs = phamerator_manage_db.get_members_of_pham(self.c, phamName)
    memberPhages, self.nonMemberPhages = [], []
    for GeneID in GeneIDs:
      PhageID = phamerator_manage_db.get_PhageID_from_GeneID(self.c, GeneID)
      if PhageID not in memberPhages: memberPhages.append(PhageID)
    totalPhages = phamerator_manage_db.get_PhageIDs(self.c)
    for p in totalPhages:
      if p not in memberPhages: self.nonMemberPhages.append(phamerator_manage_db.get_phage_name_from_PhageID(self.c, p))
    self.l = []
    self.genes = []

    for a in GeneIDs:
      for b in GeneIDs:
        if a != b:
          for gene in [a, b]:
            if gene not in self.genes: self.genes.append(gene)
          clustalwScore, blastScore = phamerator_manage_db.get_scores(self.c, a, b)
          if clustalwScore >= 0.275: self.l.append((a, b, 'clustalw',clustalwScore))
          if blastScore and blastScore <= 0.0001: self.l.append((a, b, 'blast',blastScore))
    self.phamCircle = PhamDisplay.PhamCircle(phamName, self.c,verbose=True,radius=self.radius)
    if self.alignmentColor == True:
      self.phamCircleCanvas.set_root_item_model(self.phamCircle.create_canvas_model(self.nonMemberPhages, self.genes, self.l,adjustment,self.threshold,blastColor='#ff0000', clustalwColor='#0000ff'))
    else:
      phamColorFromDataBase = self.db.select('pham_color','color',name = phamName)[0][0]
      self.phamCircleCanvas.set_root_item_model(self.phamCircle.create_canvas_model(self.nonMemberPhages, self.genes, self.l,adjustment,self.threshold,allColor = phamColorFromDataBase))
 
    """x, y = (600, 500)
    self.phamCircleCanvas.set_size_request(x, y)
    self.defaultPhamCircleCanvasSize = (x, y)
    self.phamCircleCanvas.show()
    self.window.window.set_cursor(None)
    return False"""
    
    self.current_phamCircle = self.cachedir + filename
    self.phamCircleCanvas.set_bounds(0,0, 10000, 10000)
    surface = cairo.SVGSurface (self.current_phamCircle, 15*72, 15*72)
    cr = cairo.Context (surface)
    cr.translate (10, 0)
    self.phamCircleCanvas.render (cr, None, 0.1)
    cr.show_page()
    string = "phamCircle " + str(phamName) + " generated\n"
    print ">" + string
    return string
    
  def get_phamCircle(self):
    
    myFile = open(self.current_phamCircle)
    string = myFile.read()
    myFile.close()
    print "\n>phamCircle sent\n"
    return string
   
  def get_unique_phams(self):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_unique_phams(self.c)
   
  def get_phages(self,PhageID=None, name=None):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phages(self.c,PhageID=PhageID,name=name)
  
  def get_phageID_from_pham(self,phamName):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phageID_from_pham(self.c,phamName)

  def get_length_of_genome(self,PhageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_length_of_genome(self.c,PhageID)
      
  def get_phage_name_from_PhageID(self, PhageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phage_name_from_PhageID(self.c, PhageID)
  
  def get_PhageID_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_PhageID_from_GeneID(self.c, GeneID)
  
  def get_PhageIDs(self):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_PhageIDs(self.c)
  
  def get_phage_name_from_GeneID(self,GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phage_name_from_GeneID(self.c, GeneID)
  
  def get_gene_number_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_gene_number_from_GeneID(self.c, GeneID)
  
  def get_gene_name_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_gene_name_from_GeneID(self.c, GeneID)
  
  def get_gene_start_stop_length_orientation_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_gene_start_stop_length_orientation_from_GeneID(self.c, GeneID)
  
  def get_name_from_PhageID(self, PhageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_name_from_PhageID(self.c, PhageID)
  
  def get_PhageID_from_name(self, name):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_PhageID_from_name(self.c, name)
  
  def get_phams(self):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phams(self.c)

  def get_phams_from_PhageID(self,phageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_phams_from_PhageID(self.c,phageID)

  def get_number_of_pham_members(self, phamName, PhageID=None):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_number_of_pham_members(self.c, phamName, PhageID=PhageID)
  
  def get_translation_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_translation_from_GeneID(self.c, GeneID)
  
  def get_seq_from_GeneID(self, GeneID, extra=None):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_seq_from_GeneID(self.c, GeneID, extra=extra)
  
  def get_seq_from_PhageID(self, PhageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_seq_from_PhageID(self.c, PhageID)
  
  def get_members_of_pham(self, phamName):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_members_of_pham(self.c, phamName)
  
  def get_PhageID_members_of_pham(self, phamName):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_PhageID_members_of_pham(self.c, phamName)
  
  def get_pham_from_GeneID(self, GeneID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_pham_from_GeneID(self.c, GeneID)
  
  def get_GeneIDs(self, type=None, PhageID=None):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_GeneIDs(self.c, type=type, PhageID=PhageID)
  
  def get_genes_from_PhageID(self, PhageID):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_genes_from_PhageID(self.c, PhageID)
  
  def get_all_scores(self, alignmentType='both'):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_all_scores(self.c, alignmentType=alignmentType)
  
  def get_relatives(self, GeneID, alignmentType='both', blastThreshold=None, clustalwThreshold=None):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_relatives(self.c, GeneID, alignmentType=alignmentType, blastThreshold=blastThreshold, clustalwThreshold=clustalwThreshold)
  
  def get_scores(self, query, subject):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_scores(self.c, query, subject)
  
  def get_fasta_from_pham(self, phamName):
    self.c = db_conf.db_conf(username=self.username,password=self.password,server=self.server,db=self.database).get_cursor()
    self.db = pham.db(c = self.c)
    return phamerator_manage_db.get_fasta_from_pham(self.c, phamName)






###################################################################    
server = SOAPpy.SOAPServer(("hatfull12.bio.pitt.edu", 31415))


SOAP = phageSOAP()
server.registerObject(SOAP) 
print "\n>hello matt...how are we doing today?\n"
os.system("/usr/games/fortune") 
print "\n>server started\n" 
server.serve_forever()

