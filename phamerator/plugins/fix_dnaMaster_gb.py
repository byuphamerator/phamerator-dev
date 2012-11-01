#!/usr/bin/python

import sys, os, string

def fix(tally, dirname, filenames):
  for filename in filenames:
    if os.path.isdir(os.path.join(dirname, filename)):
      print 'ignoring directory %s...' % filename
      continue
    if filename.endswith('.fixed'):
      print 'ignoring file %s' % filename
      continue
    print 'processing %s...' % filename
    infile = open(os.path.join(dirname, filename), 'U')
    
    data=infile.read()
    udata=data.decode("utf-8")
    asciidata=udata.encode("ascii","ignore")
    
    #print infile.newlines
    outfile = open(os.path.join(dirname, filename + '.fixed'), 'w')
  
    lines = asciidata.split('\n')
    locusline = lines.pop(0)
    #print locusline
  
    locusline = locusline.replace('.dnam5', '   ')
    #LOCUS       bakaDRAFTcabx.dnam5   111688 bp    DNA     circular     13-FEB-2010
    #LOCUS       angelica               50310 bp    DNA     linear       16-FEB-2010
  
    #try:
    #  locus, phage, length, bp, DNA, lin_or_circ, ENV, date = locusline.split()
    #except:
    #  locusline = locusline + lines.pop(0)
    #  locusline = locusline.replace('\n', '   ')

    if len(locusline.split()) == 8:
      locus, phage, length, bp, DNA, lin_or_circ, ENV, date = locusline.split()
    elif len(locusline.split()) == 7:
      locus, phage, length, bp, DNA, lin_or_circ, date = locusline.split()
    else:
      print 'unrecognized LOCUS line'
      print locusline
      print 'giving up on file %s' % filename
      tally['failures'] += 1
      continue
    phage = phage[0:21]
  
    newlocusline = locus + (' ' * 7)
    newlocusline = newlocusline + phage + (' ' * (28-len(phage)-len(length)))
    newlocusline = newlocusline + length
    newlocusline = newlocusline + ' ' + bp + (' ' * 4)
    newlocusline = newlocusline + DNA + (' ' * 5)
    newlocusline = newlocusline + lin_or_circ + (' ' * (13-len(lin_or_circ)))
    newlocusline = newlocusline + date
  
    #print newlocusline
    outfile.write(newlocusline)
    outfile.write('\n')
    #outfile.write(lines)
  
    for line in lines:
      line = line.replace('\r\n', '')
      # make the organism name be the last text after a space in its name
      if string.find(line, '                     /organism') != -1:
        phage_name = line.split('"')[1].split(' ')[-1]
        line = '                     /organism="%s"' % phage_name
      outfile.write(line)
      outfile.write('\n')
    tally['successes'] += 1

tally = {'successes': 0, 'failures': 0}
if os.path.isdir(sys.argv[1]):
  os.path.walk(sys.argv[1], fix, tally)

elif os.path.isfile(sys.argv[1]):
  fix(tally, [sys.argv[1]])

print '\nsuccessfully processed %s phages' % tally['successes']
if tally['failures']:
  print '%s files could not be processed' % tally['failures']
