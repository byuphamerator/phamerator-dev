#!/usr/bin/env python

from scipy import array, reshape, sqrt, identity

# nDimPoints: list of n-dim tuples
# distFunc: calculates the distance based on the differences
# Ex: Manhatten would be: distFunc=sum(deltaPoint[d] for d in xrange(len(deltaPoint)

def calcDistance(nDimPoints, 
                 distFunc=lambda deltaPoint: sqrt(sum(deltaPoint[d]**2 for d in xrange(len(deltaPoint))))):
  nDimPoints = array(nDimPoints)
  print 'nDimPoints:', nDimPoints
  dim = len(nDimPoints[0])
  print 'dim:', dim
  delta = [None]*dim
  print 'delta:', delta
  for d in xrange(dim):
    print 'd:', d
    data = nDimPoints[:,d]
    print 'data:', data
    delta[d] = abs(data - reshape(data,(len(data),1))) # computes all possible combinations
    print 'delta['+str(d)+']', delta[d]
  print 'delta:', delta
  dist = distFunc(delta)
  print 'dist:', dist
  dist = (dist + identity(len(data)))*dist.max() # eliminate self matching
  print 'returning dist:', dist
  # dist is the matrix of distances from one coordinate to any other
  return dist

def calcDistanceMatrix(nDimPoints, 
                       distFunc=lambda deltaPoint: sqrt(sum(deltaPoint[d]**2 for d in xrange(len(deltaPoint))))):
  nDimPoints = array(nDimPoints)
  dim = len(nDimPoints[0])
  delta = [None]*dim
  for d in xrange(dim):
    data = nDimPoints[:,d]
    delta[d] = data - reshape(data,(len(data),1)) # computes all possible combinations

  dist = distFunc(delta)
  print 'dist:', dist, 'is a:', type(dist)
  try: dist = (dist + identity(len(data)))*dist.max() # eliminate self matching
  except:
    print 'Error!!!'
    print 'dist:', dir(dist)
    print type(dist)
  # dist is the matrix of distances from one coordinate to any other
  return dist

from numpy.matlib import repmat, repeat
def calcDistanceMatrixFastEuclidean(points):
  numPoints = len(points)
  distMat = sqrt(sum((repmat(points, numPoints, 1) - repeat(points, numPoints, axis=0))**2, axis=1))
  return distMat.reshape((numPoints,numPoints))

from numpy import mat, zeros, newaxis
def calcDistanceMatrixFastEuclidean2(nDimPoints):
  nDimPoints = array(nDimPoints)
  n,m = nDimPoints.shape
  delta = zeros((n,n),'d')
  for d in xrange(m):
    data = nDimPoints[:,d]
    delta += (data - data[:,newaxis])**2
  return sqrt(delta)


def main():
  distanceMatrixFunc = "calcDistanceMatrix"
  points = [[0, 0, 0], [1.0, 1, 1], [4, 5, 6], [10,10,10]]
  dm = eval("%s(points)"%distanceMatrixFunc)
  print dm

if __name__ == '__main__':
  main()
