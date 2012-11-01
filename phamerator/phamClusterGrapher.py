#!/usr/bin/env python

# Usage:
#   graph_directory.py directory [output_file]

import yapgvb
import user, os, sys, operator

def is_pham(item):
  #print 'item:', item
  if type(item[0]) == type(int()):
    #print item, 'is a pham'
    return True
  else: return False

def is_cluster(item):
  #print item, 'is a group'
  for i in item:
    if type(i) != type([]): return False
  return True

def contains_member(pham, phage):
  lnames = ['', 'bxb1', 'che8', 'cjw1', 'bxz2', 'che9c', 'rosebush', 'corndog', 'che9d', 'bxz1', 'omega', 'barnyard', 'pg1', 'u2', 'bethlehem', 'd29', 'l5', '244', 'catera', 'che12', 'cooper', 'halo', 'llij', 'orion', 'pbi1', 'plot', 'pmc', 'pipefish', 'qyrzula', 'wildcat', 'tm4']
  #print 'pham:', pham, 'phage:', phage
  if not phage:
    #print 'no phage name was given'
    return False
  index = lnames.index(phage)
  if pham[index] > 0: return True
  else: return False
 
def generate_pham_graph(graph, items, parent=None, phage=None, current=-1):
  # Create a new directed graph
  if is_pham(items):
    if not parent:
      print 'this pham is an orphan!'
      sys.exit()
    phamName = str(items[0])
    if contains_member(items, phage):
      fillcolor = 'green'
      color = 'blue'
      shape = 'ellipse'
    else:
      fillcolor = 'white'
      color = 'black'
      shape = 'ellipse'
    nodes[phamName] = graph.add_node(phamName, label='pham %s'%phamName, color=color, fillcolor=fillcolor, shape=shape)
    print nodes[parent] >> nodes[phamName]            
  elif is_cluster(items):
    for item in items:
      clusterName = str(current+1)
      nodes[clusterName] = graph.add_node(clusterName, label='group %s'%clusterName)
      generate_pham_graph(graph, item, parent=clusterName, phage=phage, current=clusterName)
  return graph

if __name__ == '__main__':
  nodes = {}
  clusters = eval(open('graphviz_input.txt').read())
  graph = yapgvb.Digraph()

  # Did the user specify a filename on the command line?
  output_file = sys.argv[1]
  
  if output_file is None:
    output_file = 'output.png'

  if len(sys.argv) > 2: phage = sys.argv[2]
  else: phage = None
  print 'phage:', phage
    
  print "Generating pham structure graph... Ctrl-C to terminate"

  for n, item in enumerate(clusters):
    graph = generate_pham_graph(graph, item, phage=phage, current=n)
        
  # layout with circo algorithm
  print "Using circo engine for layout..."
  graph.layout(yapgvb.engines.circo) 
    
  # render!
  print "Rendering %s..." % output_file
  graph.render(output_file)

  print sys.argv
