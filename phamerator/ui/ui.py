import os

class gladeFile:
  def __init__(self):
    gladeFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', "phamerator.ui")
    if os.path.exists(gladeFilePath):
      self.filename = gladeFilePath
    else:
      self.filename = os.path.join('/usr/share/phamerator/glade/',"phamerator.ui")
