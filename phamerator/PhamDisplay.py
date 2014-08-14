import sys
import gobject
import gtk
import goocanvas
import math
import random
import re, db_conf
from phamerator_manage_db import *

class PhamCircle:
  
  """a class for drawing phamily circles on a pygoocanvas"""
  
  def __init__(self, phamName, c,**kargs):
    
    """initializes circle center and radius"""
    print 'creating PhamCircle...'
    try:
        self.radius = kargs["radius"]
    except:
        self.radius = 750
    self.h, self.k = self.radius + 400,self.radius + 240
    """the above numbers determine where the phamily circle is displayed on the page"""
	
    self.c = c
    self.phamName = phamName
    if 'verbose' in kargs.keys(): 
      self.verbose = True
    else:
      self.verbose = False
    #self.verbose = True
  def set_threshold(self,thresh):
    self.threshold = thresh
  def getName(self,geneID):
    exp = re.compile('\d+[.]*\d*$')
    try:
      name = get_phage_name_from_GeneID(self.c, geneID) + " (gp" + str(int((exp.search(get_gene_name_from_GeneID(self.c, geneID))).group().strip())) + ")"
    except:
      try:
        name = get_phage_name_from_GeneID(self.c, geneID) + ' (gp' + str(float(get_gene_name_from_GeneID(self.c, geneID))) + ')'
      except:
        name = get_phage_name_from_GeneID(self.c, geneID) + ' (gp' + get_gene_name_from_GeneID(self.c, geneID) + ')'
    return name

   
  def create_canvas_model(self, nonMemberPhages, geneList, inputList,adjustment,threshold,**kargs):
    
    """Creates the canvas model to be drawn to goocanvas.  This includes the polygon itself, and also the arcs connecting related sides"""
    
    #########################################
    
    """Colors are grabbed and color boolean set"""
    if 'allColor' in kargs.keys():
      self.allColor = kargs['allColor']
      self.singleColor = True
    else: 
      self.singleColor = False
      for key in kargs.keys():
        #bothColor = kargs[bothColor]
        self.clustalwColor = kargs['clustalwColor']
        self.blastColor = kargs['blastColor']
      
    #########################################
    
    """Labels containing gene/genome data are created and sorted alphabetically according to their comparator string """
    self.adjustment = adjustment
    self.threshold = threshold
    self.nonMemberPhages = nonMemberPhages
    self.geneList = geneList
    self.inputList = InputData(inputList)
    labels = []
    rawLabels = nonMemberPhages + geneList
    self.root = goocanvas.GroupModel() 
    self.polygon_n_labels = goocanvas.GroupModel()
    for nMP in nonMemberPhages:
      comparator = nMP
      labels.append(Label(nMP, 'phage',comparator))
    
    for gL in geneList:
      comparator = self.getName(gL)
      labels.append(Label(gL, 'gene',comparator))
    clusters = {}
    for clust in get_clusters(self.c, include_unclustered=False):
      clusters[clust] = Cluster(clust)

    clusters['NONMEM'] = Cluster('NONMEM')

    for label in labels:
      cluster = get_cluster_from_PhageID(self.c, get_PhageID_from_name(self.c,label.comparator.split(' ')[0]))
      if cluster in clusters:
        clusters[cluster].add(label)
      else:
        clusters['NONMEM'].add(label)
    self.clusters = clusters
    for clust in get_clusters(self.c, include_unclustered=False):
      print "################################################"
      print clust
      print "################################################"
      for lbl in clusters[clust].getLabels():
        print lbl.comparator
    print "##############################################"
    print "NON MEMBERS"
    print "##############################################"
    for lbl in clusters["NONMEM"].getLabels():
        print lbl.comparator
    #########################################
    
    """Set up all constants and initialize some variables to be used for drawing polygon/arcs"""
    radius, h, k = self.radius, self.h, self.k
    self.centers = {}
    numItems = len(geneList) + len(nonMemberPhages)
    self.numItems = numItems
    rectWidth = (2*math.pi*radius)/numItems
    rectHeight = rectWidth/4
    self.rectHeight = rectHeight
    font = str(int(rectWidth/4))
    #font = '6'
    bigFont =  str(int((rectWidth/2)+10))
    #bigFont = '50'
    xPos = h-(rectWidth/2)
    yPos = k-radius
    rotationIncrement = 360.0/numItems
    current = 0
    currentRotation = 270
    r = g = b = 0
    fill = 'gray'
    labelPad = radius * 0.33
    print 'displaying pham %s' % self.phamName
    item =goocanvas.TextModel(text='Pham %s' % str(self.phamName),
          x=self.h, y=self.k/15.0, #(self.k - self.radius),
          anchor=gtk.ANCHOR_CENTER,
          font="Arial " + bigFont)
		  """the above code determines the position of the Pham name label"""
    self.polygon_n_labels.add_child(item, -1)
    #########################################
    
    """Iterate through all labels containing genome/gene names and draw them to n-sided polygon."""
    lastY = yPos - 10
    cluster_list = clusters.keys()
    cluster_list.sort()
    color_counter = 0
    self.clusterCenters = {}
    color_list = ['#ea55ff','#ffaaea','#ff5f00','#d7b9a8','#e47532','#ffdcc7','#6aff55','#ceffc7','#e0ff00','#1cffff','#9c38ff','#bb7ef8','#b8ff71','#ff5555','#ffaaaa','#1c55ff']
    for cluster in cluster_list:
      if color_counter < len(color_list):
        current_color = color_list[color_counter]
        color_counter = color_counter + 1
      else:
        current_color = fill
      labels = clusters[cluster].getLabels()
      first = 0
      last = len(labels)-1
      for label in labels:
        if currentRotation >= 360:
          currentRotation = currentRotation - 360

        if currentRotation == 0:
          signX = 1
          signY = -1
        elif currentRotation > 0 and currentRotation < 90:
          signX = 1
          signY = 1
        elif currentRotation<180 and currentRotation >=90:
          signX = -1
          signY = 1
        elif currentRotation<270 and currentRotation >=180:
          signX = -1
          signY = -1
        elif currentRotation >= 270 and currentRotation < 360:
          signX = 1
          signY = -1
        else:
          print 'something is messed up'
          sys.exit()
        rgb = '#%02x%02x%02x' % (r,g,b)
        centerX = h +  (math.cos(math.radians(currentRotation))*radius)
        centerY = k +  (math.sin(math.radians(currentRotation))*radius)
        self.centers[label.text] = [centerX,centerY]
        if labels[first] == label:
          self.clusterCenters[cluster] = [[centerX,centerY],]
        if labels[last] == label:
          self.clusterCenters[cluster].append([centerX,centerY])
        item = goocanvas.RectModel(x=centerX-(rectWidth/2.0), y=centerY+(-1*rectHeight), width=rectWidth, height=rectHeight,
                        line_width=1.5,
                        radius_x=1.0,
                        radius_y=1.0,
                        stroke_color=rgb,
                        fill_color=current_color)
        item.rotate(currentRotation+90, centerX,centerY)
        self.polygon_n_labels.add_child(item, -1)
        if signX == 1:
          textX = h +  (math.cos(math.radians(currentRotation))*(radius+rectHeight+6))
          if signY == 1:
            textY = k +  (math.sin(math.radians(currentRotation))*(radius+rectHeight+6))
            anchor = gtk.ANCHOR_NORTH_WEST
          if signY == -1:
            textY = k +  (math.sin(math.radians(currentRotation))*(radius+rectHeight+6)) 
            anchor = gtk.ANCHOR_SOUTH_WEST
        else:
          textX = h +  (math.cos(math.radians(currentRotation))*(radius+rectHeight+6))
          if signY == 1:
            textY = k +  (math.sin(math.radians(currentRotation))*(radius+rectHeight+6))
            anchor = gtk.ANCHOR_NORTH_EAST
          if signY == -1:
            textY = k +  (math.sin(math.radians(currentRotation))*(radius+rectHeight+6))
            anchor = gtk.ANCHOR_SOUTH_EAST
        if label.type == 'phage': text = label.text
        else:
          text = label.comparator
      
        if (90-rotationIncrement)<currentRotation<(90+rotationIncrement) or (270-rotationIncrement)<currentRotation<(270+rotationIncrement):
          textY = textY + (signY*int(font)*3)
        if (90-(rotationIncrement*2))<currentRotation<(90-rotationIncrement) or (90+rotationIncrement)<currentRotation<(90+rotationIncrement*2) or (270-(rotationIncrement*2))<currentRotation<(270-rotationIncrement) or (270+rotationIncrement)<currentRotation<(270+(rotationIncrement*2)):
          textY = textY + (signY*int(font)*2)
        if (90-(rotationIncrement*3))<currentRotation<(90-(rotationIncrement*2)) or (90+rotationIncrement*2)<currentRotation<(90+rotationIncrement*3) or (270-(rotationIncrement*3))<currentRotation<(270-(rotationIncrement*2)) or (270+(rotationIncrement*2))<currentRotation<(270+(rotationIncrement*3)):
          textY = textY + (signY*int(font))
        textModel =goocanvas.TextModel(text=text,
                  x=textX, y=textY,
                  anchor=anchor,
                  #font="Arial " + str(rectHeight))
                  font="Arial " + font)
        lastY = textY
        self.polygon_n_labels.add_child(textModel, -1)
        if self.verbose == True:
          print str(text) + " at rotation of " + str(currentRotation) + " degrees, with a Y-sign value of " + str(signY) + "\n"
        currentRotation = currentRotation + rotationIncrement
    

    
      
         
    self.root.add_child(self.polygon_n_labels,-1)
    self.first_time = True
    root = self.update_arc_groupModel(adjustment)
    return root
    

  def showClusters(self):
      self.clusterGroup = goocanvas.GroupModel()
      cluster_list = self.clusters.keys()
      cluster_list.sort()
      for cluster in cluster_list:
        startx,starty = self.clusterCenters[cluster][0]
        endx,endy = self.clusterCenters[cluster][1]
        startAngle = math.atan2(starty - self.k,startx - self.h)
        endAngle = math.atan2(endy - self.k,endx - self.h)
        startx,starty = self.h + (math.cos(startAngle)*(6 + self.radius)),self.k + (math.sin(startAngle)*(6 + self.radius))
        endx,endy = self.h + (math.cos(endAngle)*(6 + self.radius)),self.k + (math.sin(endAngle)*(6 + self.radius))
        """<path d="M275,175 v-150 a150,150 0 0,0 -150,150 z" fill="yellow" stroke="blue" stroke-width="5" />""" #example path for pie shape
        """      item = goocanvas.PathModel(data=svgPathString,stroke_color_rgba=self.colorData,line_width=lineWidth)""" #example pygoocanvas call
        d = "M%s,%s A%s,%s 0 0,1 %s,%s" %(startx,starty,(self.radius+5),(self.radius+5),endx,endy)
        item = goocanvas.PathModel(data=d,stroke_color="#969696",line_width=4)
        self.clusterGroup.add_child(item,-1)
      self.root.add_child(self.clusterGroup,2)

  def hideClusters(self):
    self.root.remove_child(2)


  def update_arc_groupModel(self,adjustment):
    """Iterate through all nodes containing arc data, and draw them to the n-sided polygon """
    if adjustment != None:
      self.adjustment = adjustment
    if self.first_time == False:
      self.hideClusters()
      current =  self.root.get_child(1)
      self.root.remove_child(1)
    self.first_time = False
    self.arcGroup = goocanvas.GroupModel()
    for node in self.inputList.nodeList:
      if node.relation >= adjustment:
        alpha = hex(255)
        
      else:
        scaler = ((node.relation/adjustment) - self.threshold)/.725
        if scaler < 0:
          scaler = 0
        if scaler > 1:
          scaler = 1
        scaler = 255 * scaler
        alpha = hex(int(scaler))
      if alpha > 0x0:
        if self.verbose == True:
          print 'drawing arc from', self.getName(node.fromGene), 'to', self.getName(node.toGene),"\n",'using',node.clust_blast,"\n",'with scaled score ', node.relation,"\n",'and unscaled score',node.unScaledRelation,"\n","with an adjustment of",adjustment,"\n","and a score threshold of",str(self.threshold),"\n"
        if self.singleColor == True:
          self.arc = Arc(self.centers[node.fromGene],self.centers[node.toGene],node.relation, self.h, self.k, self.radius,self.allColor,alpha)    
        else:
          clust_blast_info = node.clust_blast
          try:
            if clust_blast_info == "clustalw":
              self.arc = Arc(self.centers[node.fromGene],self.centers[node.toGene],node.relation, self.h, self.k, self.radius,self.clustalwColor,alpha)
            elif clust_blast_info == "blast":
              self.arc = Arc(self.centers[node.fromGene],self.centers[node.toGene],node.relation, self.h, self.k, self.radius,self.blastColor,alpha)
            else:
               self.arc = Arc(self.centers[node.fromGene],self.centers[node.toGene],node.relation, self.h, self.k, self.radius,self.bothColor,alpha)
          except KeyError:
            pass
          #if hasattr(self, 'arc'):
      self.arcGroup.add_child(self.arc.draw_arc(self.radius), -1)
    self.root.add_child(self.arcGroup,-1)
    self.showClusters()
    return self.root
    
    #########################################

    
      
        
  """This is our handler for the "item-view-created" signal of the GooCanvasView.  We connect to the "button-press-event" signal of new rect views."""
  def on_item_view_created (self, view, item_view, item):
    if isinstance(item, goocanvas.Rect):
      item_view.connect("button_press_event", on_rect_button_press)
  """This handles button presses in item views. We simply output a message to the console."""
  def on_rect_button_press (self, view, target, event):
    print "rect item received button press event" + str(target)
    return True
  """This is our handler for the "delete-event" signal of the window, which is emitted when the 'x' close button is clicked. We just exit here."""
  def on_delete_event(self, window, event):
    raise SystemExit
  
  #########################################
  """End create_canvas_model"""
  #########################################

  
class Arc:
  
  """a class that holds information about where to draw arcs"""
  
  def __init__(self, p0, p1, relation, h, k, radius,colorData,alpha):
    colorData = colorData.strip("#")
    alpha = str(alpha)
    alpha = alpha.replace('0x', '')
    if len(alpha) == 1:
      alpha = "0" + alpha
    self.colorData = int(str(colorData+alpha),16)
    self.points = [p0, p1]
    self.h, self.k, self.radius = h, k, radius
    self.relation = relation
  
  def draw_arc(self, radius):
    
    """Draw the arc connecting two related genes/genomes"""
    
    #########################################
    
    p0, p1 = self.points
    toX, toY = p0[0], p0[1]
    fromX, fromY = p1[0], p1[1]
    lineWidth = self.relation*3
    if toX < fromX:
      toX, fromX, toY, fromY = self.swap_to_and_from(toX, fromX, toY, fromY)
    if toX == fromX:
      if fromY > toY:
        toX, fromX, toY, fromY = self.swap_to_and_from(toX, fromX, toY, fromY)
    dx = toX-fromX
    dy = toY-fromY
    distance = math.sqrt(dx**2+dy**2)
    if ((2*radius)-distance)<1.5:
      linedata = "M" + str(fromX) + "," + str(fromY) + "L" + str(toX) + "," + str(toY)
      item = goocanvas.PathModel(data=linedata,stroke_color_rgba=self.colorData, line_width=lineWidth)
    else:
      svgPathString = self.make_svg_string(fromX, fromY, toX, toY)
      item = goocanvas.PathModel(data=svgPathString,stroke_color_rgba=self.colorData,line_width=lineWidth)
      if dx == 0:
        rotation = 90
      else: 
        rotation = math.degrees(math.atan(float(dy)/dx))
      item.rotate(rotation,fromX,fromY)
    return item
  
  #########################################
  
  def swap_to_and_from(self, toX, fromX, toY, fromY):
    
    """Swap the x and y coordinates to ensure the arc will be drawn from left to right """
    
    return fromX, toX, fromY, toY
  
  
  def make_svg_string(self, fromX, fromY, toX, toY):
    
    """Create the SVG string that describes the arc being drawn """
    
    #########################################
    
    dx = toX-fromX
    dy = toY-fromY
    distance = math.sqrt(dx**2+dy**2)
    if dx==0:
      angleFromPointToPoint=270
    else: 
      angleFromPointToPoint = math.degrees(math.atan(float(dy)/dx))
    dxCenter = self.h-fromX
    dyCenter = self.k-fromY
    if dxCenter==0:
      if dyCenter > 0: angleFromPointToCenter=270 # remove if
      else: angleFromPointToCenter=90 # delete me
    else:
      angleFromPointToCenter = math.degrees(math.atan(float(dyCenter)/dxCenter))
    if fromX == self.h: 
      if angleFromPointToCenter == 90: sign = 1
      else: 
        sign = -1      
    if fromX < self.h:
      if angleFromPointToPoint > angleFromPointToCenter:
        sign = 1
      if angleFromPointToPoint < angleFromPointToCenter:
        sign = -1
    if fromX > self.h:
      if angleFromPointToPoint > angleFromPointToCenter:
        sign = -1
      if angleFromPointToPoint < angleFromPointToCenter:
        sign = 1
    toX,toY = fromX+distance, fromY
    con1y = fromY+(sign*(math.sin(60)) * distance *.3)
    con2y = con1y
    con1x = fromX + (0.25*distance)
    con2x = fromX + (0.75*distance)
    p = "M%s,%s "           \
        "C%s,%s "           \
        "%s,%s "            \
        "%s,%s "        %   (
                            fromX,fromY,    #absolute start point
                            con1x,con1y,
                            con2x,con2y,
                            toX,toY
                            )                                   
    return p

  #########################################
  """End Arc"""
  #########################################


class Label:
  
  """a class that holds information about phage and gene labels for pham circles"""
  
  #########################################
  
  def __init__(self, text, type, comparator):
    self.text = text
    self.type = type
    self.comparator = comparator
  def __cmp__(self, other):
    this = self.comparator
    other = other.comparator
    
    if this.rfind(" (gp")!= -1 and other.rfind(" (gp")!= -1:
    
      thisTuple = this.split(" (gp")
      otherTuple = other.split(" (gp")
                                
      thisFirst = thisTuple[0]
      otherFirst = otherTuple[0]

      
      try: thisLast = float(thisTuple[1].replace(")",""))
      except: thisLast = thisTuple[1].replace(")","")
      try: otherLast = float(otherTuple[1].replace(")",""))
      except: otherLast = otherTuple[1].replace(")","")

    
      if thisFirst<otherFirst:
        return -1
      elif thisFirst>otherFirst:
        return 1
      elif thisLast==otherLast:
        return 0
      elif thisLast<otherLast:
        return -1
      elif thisLast>otherLast:
        return 1
    else:
      if this>other:
        return 1
      if this<other:
        return -1
      if this == other:
        return 0 

  #########################################
  """End Label"""
  #########################################


  
  
  
#########################################  
class Node:
  """An inner class containing the actual data """
  def __init__(self,fromGene,toGene,clust_blast,rel,rel2):   
    self.fromGene = fromGene
    self.toGene = toGene
    self.clust_blast = clust_blast
    self.relation = rel
    self.unScaledRelation = rel2
    self.ACONSTANT = 3

  def __cmp__(self, other):
    if self.relation > other.relation:
      return -1
    elif self.relation < other.relation:
      return 1
    else:
      return 0



class InputData:
  """A class that holds input data and enables it to be sorted by relation score"""
  def __init__(self,inputlist):
    self.inputlist = inputlist
    self.nodeList = []
    def convert_score(score):
      '''convert the score from a very small number to one that is probably between 0 and 200'''
      score = '%e' % score
      if score.find('e-')   != -1: score = int(score.split('e-')[1])
      elif score == 0.0 and score.find('e+') != -1: score = int(score.split('e+')[1])
      if score > 3 and score < 21: score = 0.325
      elif score >= 21 and score <  39: score = 0.325 + ((1-.325)/9)
      elif score >= 39 and score <  57: score = 0.325 + ((1-.325)/9)*2
      elif score >= 57 and score <  75: score = 0.325 + ((1-.325)/9)*3
      elif score >= 75 and score <  93: score = 0.325 + ((1-.325)/9)*4
      elif score >= 93 and score < 111: score = 0.325 + ((1-.325)/9)*5
      elif score >=111 and score < 129: score = 0.325 + ((1-.325)/9)*6
      elif score >=129 and score < 147: score = 0.325 + ((1-.325)/9)*7
      elif score >=147 and score < 165: score = 0.325 + ((1-.325)/9)*8
      elif score >=165 and score < 183: score = 0.325 + ((1-.325)/9)*9
      elif score >=183 or score == 0.0: score = 1
      return score
    for currentFromGene,currentToGene,clust_blast_string,unScaledRelation in inputlist:
      if clust_blast_string == 'blast': scaledRelation = convert_score(unScaledRelation)
      else:
        scaledRelation = unScaledRelation
        unScaledRelation = "none"
      self.nodeList.append(Node(currentFromGene,currentToGene,clust_blast_string,scaledRelation,unScaledRelation))
    self.nodeList.sort() 

#########################################
"""End InputData """
#########################################


class Cluster:
  def __init__(self,name):
    self.name = name
    self.labels = []

  def add(self,label):
    self.labels.append(label)

  def getLabels(self):
    self.labels.sort()
    return self.labels

  def __cmp__(self, other):
    if self.name > other.name:
      return 1
    elif self.name < other.name:
      return -1
    else:
      return 0

def main(argv):
  phamC = PhamCircle("test","")
  print "hello main"
  window = gtk.Window()
  window.set_default_size(800, 800)
  window.show()
  #window.connect("delete_event", on_delete_event)
  scrolled_win = gtk.ScrolledWindow()
  scrolled_win.set_shadow_type(gtk.SHADOW_IN)
  scrolled_win.show()
  window.add(scrolled_win)
  phamName = "11"
  c = db_conf.db_conf(username='anonymous',password='anonymous',server='localhost',db='SEA').get_cursor()

  GeneIDs = get_members_of_pham(c, phamName)
  if (True):
    memberPhages, nonMemberPhages = [], []
    for GeneID in GeneIDs:
      PhageID = get_PhageID_from_GeneID(c, GeneID)
      if PhageID not in memberPhages: memberPhages.append(PhageID)
    totalPhages = get_PhageIDs(c)
    for p in totalPhages:
      if p not in memberPhages: nonMemberPhages.append(get_phage_name_from_PhageID(c, p))
    l = []
    genes = []

    genes = GeneIDs
    for a in GeneIDs:
      clustalwScores, blastScores = get_pham_scores(c, a)
      for cs in clustalwScores:
        if cs[2] >= 0.325: l.append((cs[0], cs[1], 'clustalw',cs[2]))
      for bs in blastScores:
        if bs[2] <= 1e-50: l.append((bs[0], bs[1], 'blast',bs[2]))

    phamCircle = PhamCircle(phamName, c)
    adjustment = 0.325
    phamCircleCanvas = goocanvas.Canvas()
    scrolled_win.add(phamCircleCanvas)
    phamCircleCanvas.set_root_item_model(phamCircle.create_canvas_model(nonMemberPhages, genes, l,adjustment,'27.0',blastColor='#ff0000', clustalwColor='#0000ff'))
    
 
    x, y = (800, 800)
    phamCircleCanvas.set_size_request(x, y)
    defaultPhamCircleCanvasSize = (x, y)
    phamCircleCanvas.show()
    window.window.set_cursor(None)
  
  gtk.main()

if __name__ == "__main__":
  main(sys.argv)
  
