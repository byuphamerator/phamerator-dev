import pham

class gene:
  def __init__(self, GeneID, name, start, stop, length, orientation):
    self.GeneID = GeneID
    self.name = name
    self.start = start
    self.stop = stop
    self.length = length
    self.orientation = orientation
    
  def __cmp__(self, other):
    return cmp(self.start, other.start)

  def get_pham(self):
    db = pham.db(c)
    pham = db.select('pham', name, GeneID = self.GeneID)
    return pham
