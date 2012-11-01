#!/usr/bin/env python

import os
os.environ["LD_LIBRARY_PATH"]="/usr/lib/firefox/"
import gtk
import gtkmozembed

class TinyGecko:
    def __init__(self):
        self.moz = gtkmozembed.MozEmbed()
        win = gtk.Window()
        win.set_default_size(800,800)
        win.add(self.moz)
        gtkmozembed.set_profile_path("/tmp", "foobar")
        win.show_all()
        self.moz.load_url('http://hatfull12.bio.pitt.edu:8080')
        data = '<html><head><title>Hello</title></head><body>pygtk dev</body></html>'
        self.moz.render_data(data, long(len(data)), 'file:///', 'text/html')

if __name__ == '__main__':
  TinyGecko()
  gtk.main()
