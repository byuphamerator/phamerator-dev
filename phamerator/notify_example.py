#!/usr/bin/env python

#try:
import pynotify
if pynotify.init("Phamerator"):
  n = pynotify.Notification("Phamerator Update", "alignments are ready", "file:///home/steve/Applications/git/PhamDB/phageManager_logo.png")
  n.set_hint("y", 500)
  n.attach_to_widget()
  n.show()
else:
  print "there was a problem initializing the pynotify module"
#except:
#  print "you don't seem to have pynotify installed"
