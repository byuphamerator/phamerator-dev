from distutils.core import setup
import glob

setup(name='phamerator',
      version='1.0.1',
      #py_modules=['phamerator'],
      author='Steve Cresawn',
      author_email='cresawsg@jmu.edu',
      url='http://phage.cisat.jmu.edu',
      packages=['phamerator'],
      package_dir={'phamerator': 'phamerator'},
      scripts=['phamerator/Phamerator'],
      package_data={'phamerator': ['html/*']},
      data_files=[('/usr/share/applications/', ['phamerator/phamerator.desktop']), ('/usr/share/phamerator/config/', ['phamerator/config/phamerator.conf.sample']), ('/usr/share/phamerator/glade', ['phamerator/phamerator.glade']), ('/usr/share/phamerator/glade', glob.glob('phamerator/*.svg')),('/usr/share/pixmaps/',['phamerator/pixmaps/phamerator.png']),('/usr/share/icons/hicolor/scalable/apps/',['phamerator/pixmaps/phamerator.svg'])],
      )
