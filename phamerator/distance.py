#!/usr/bin/env python

# determine the Euclidian distance between two phams

import db_conf, time, getpass
from scipy import reshape, sqrt, identity, array
from phamerator_manage_db import *

# FIXME: authentication details through getopt
password = getpass.getpass('database root password:')
c = db_conf.db_conf(username='root', password=password, server='djs-bio.bio.pitt.edu', db='Hatfull').get_cursor()
#c = db_conf.db_conf().get_cursor()

def calcDistanceMatrix(nDimPoints, 
  distFunc=lambda deltaPoint: sqrt(sum(deltaPoint[d]**2 for d in xrange(len(deltaPoint))))):
  '''calculate the Euclidian distance between a list of n-dimensional points'''
  print 'using calcDistanceMatrix'
  #time.sleep(1)
  nDimPoints = array(nDimPoints)
  print 'nDimPoints:', nDimPoints
  dim = len(nDimPoints[0])
  print 'dim:', dim
  delta = [None]*dim
  print 'delta:', delta
  for d in xrange(dim):
    data = nDimPoints[:,d]
    print 'data:', data
    delta[d] = data - reshape(data,(len(data),1)) # computes all possible combinations
    print 'delta[d]:', delta[d]
  print 'delta:', delta
  dist = distFunc(delta)
  print 'dist:', dist
  dist = dist + identity(len(data))*dist.max() # eliminate self matching # UNCOMMENT ME
  # dist is the matrix of distances from one coordinate to any other
  return dist

from numpy.matlib import repmat, repeat
def calcDistanceMatrixFastEuclidean(points):
  print 'using calcDistanceMatrixFastEuclidean'
  #time.sleep(1)
  numPoints = len(points)
  #distMat = sqrt(sum(repmat((numPoints, numPoints, 1) - repeat(points, numPoints, axis=0))**2, axis=1))
  distMat = sqrt(sum((repmat(points, numPoints, 1) - repeat(points, numPoints, axis=0))**2, axis=1))
  return distMat.reshape((numPoints,numPoints))[0,1]

from numpy import mat, zeros, newaxis
def calcDistanceMatrixFastEuclidean2(nDimPoints):
  print 'using calcDistanceMatrixFastEuclidean2'
  #time.sleep(1)
  print 'nDimPoints:', nDimPoints
  temp = nDimPoints[:]
  nDimPoints = []
  for i in temp:
    i = i [1:]
    nDimPoints.append(i)
  #temp = array([])
  #for row in nDimPoints: temp = temp + row[1:]
  #for i in nDimPoints: i.pop(0)
  nDimPoints = array(nDimPoints)
  print 'nDimPoints:', nDimPoints
  #nDimPoints = temp
  n,m = nDimPoints.shape
  delta = zeros((n,n),'d')
  for d in xrange(m):
    data = nDimPoints[:,d]
    delta += (data - data[:,newaxis])**2
  print 'delta:', delta
  print 'returning:', sqrt(delta)[0,1]
  return sqrt(delta)[0,1]

def calcDistanceMatrixFastEuclidean3(nDimPoints):
  #print 'nDimPoints:', nDimPoints
  phamNameRemoved = []
  for i in nDimPoints: phamNameRemoved.append(i[1:])
  nDimPoints = phamNameRemoved
  #print 'nDimPoints:', nDimPoints
  #time.sleep(5)
  nDimPoints = array(nDimPoints)
  #print 'nDimPoints:', nDimPoints
  n,m = nDimPoints.shape
  delta = zeros((n,n),'d')
  for d in xrange(m):
    data = nDimPoints[:,d]
    delta += (data - data[:,newaxis])**2
  #print 'delta:', delta
  return sqrt(delta[0,1])

def calculateDistance(nDimPoints):
  print 'using calculateDistance'
  
def create_score_matrix():
  '''create a matrix whose number of dimensions equals the number of genomes in the db'''
  points = []
  phages = []
  phams  = []
  r = get_phages(c, PhageID=True)
  for _ in r: phages.append(_[0])
  phages.sort()
  print phages
  r = get_phams(c)
  for _ in r:
    if _[0] not in phams: phams.append(_[0])
  print 'phams:', phams
  #phams = phams[:250]
  print 'phams:', phams
  for pham in phams:
    row = [int(pham)]
    for phage in phages:
      row.append(int(get_number_of_pham_members(c, pham, PhageID=phage)))
    if reduce(lambda x, y: x+y, row[1:]) > 1: points.append(row) # only cluster phams with >1 member
  print 'number of phams to cluster:', len(points)
  #time.sleep(5)
  return points

def main():
  matrix = create_score_matrix()
  print "matrix length", len(matrix)
  distFunc = 'calcDistanceMatrix'
  distFunc = 'calcDistanceMatrixFastEuclidean2'
  dm = eval("%s(matrix)"%distFunc)
  print dm
  
if __name__ == '__main__':
  main()
