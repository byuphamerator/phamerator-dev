#!/usr/bin/env python

import distance, time
from cluster import HierarchicalClustering
from scipy import array

class PhamCluster:
  def __init__(self):
    self.distancesComputed = 0
  def initialize_matrix(self):
    '''creates an array to be used for holding the distances'''
    self.scoreMatrix = distance.create_score_matrix()
    #self.scoreMatrix = [[1,0,0],[2, 0,1],[3,110,1],[4, 1, 1],[5,0,0]]
    #self.scoreMatrix = [(0), (1), (5)]
    #self.scorelabels = ['U2', 'L5', 'D29']
  def get_distance(self, x, y):
    '''returns a distance looked up in the matrix array'''
    #self.distancesComputed += 1
    #print self.distancesComputed
    #print 'getting distance for', x, y
    #print 'x:', x, '\ny:', y
    d = distance.calcDistanceMatrixFastEuclidean3([x, y])
    #d = distance.calcDistanceMatrixFastEuclidean3(array(x, y))
    #d = distance.calcDistanceMatrixFastEuclidean2(array(x, y))
    #print 'd:', d
    return d
    #a = self.scoreMatrix.index(x)
    #b = self.scoreMatrix.index(y)
    #print 'a:', a, '\nb:', b
    #print self.distMatrix[a][b]
    #time.sleep(5)
    #return self.distMatrix[a][b]
    #except: print 'x:', x, 'y:', y
  def calculate_distances(self):
    '''calculate the distances for all items in the array'''
    self.distMatrix = distance.calcDistanceMatrixFastEuclidean3(self.scoreMatrix)
    print 'distMatrix is a(n)', type(self.distMatrix)

def main():
  pC = PhamCluster()
  pC.initialize_matrix()
  #pC.calculate_distances()

  #print 'scoreMatrix:', pC.scoreMatrix
  #print 'distMatrix:', pC.distMatrix
  cl = HierarchicalClustering(pC.scoreMatrix, lambda x,y: pC.get_distance(x,y))
  #cutoff = raw_input('specify cutoff level:')
  cutoff = 1
  print 'using cutoff of 1'
  clusters = cl.getlevel(float(cutoff))
  print 'there are', len(clusters), 'clusters'
  print clusters
  print 'there are', len(clusters), 'clusters'

if __name__ == '__main__':
  main()
