#!/usr/bin/env python

import os, sys, time, db_conf
c = db_conf.db_conf().get_cursor()
table = sys.argv[1]
poll = int(sys.argv[2])
c.execute("SELECT COUNT(*) FROM %s" % table)
total = int(c.fetchone()[0])

pbar = os.popen("zenity --progress --auto-close --title=\"%s progress\" --text=\"\"" % table, "w", 0)
timer = poll

while 1:
  if timer == poll:
    c.execute("SELECT COUNT(*) FROM %s WHERE status = 'done'" % table)
    count = int(c.fetchone()[0])
    c.execute("COMMIT")
    p = float(count)/total*100
    percent = "%02f" % p
    pbar.write(str(percent)+'\n')
    timer = 0
  pbar.write('#'+str(count)+'/'+str(total)+' : '+str(percent)+'% '+str(timer)+'/'+str(poll)+'\n')
  timer = timer + 1
  time.sleep(1)      

try:
  import pynotify
  if pynotify.init("Phamerator"):
    n = pynotify.Notification("Phamerator Update", "doing clustalw alignments", "file:///home/steve/Applications/git/PhamDB/phageManager_logo.png")
    n.show()
  else:
    pass
    #print "there was a problem initializing the pynotify module"
except:
  pass

