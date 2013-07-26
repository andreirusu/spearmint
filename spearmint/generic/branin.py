import numpy as np
import sys
import math
import time

def branin(x, y):
  
  if x < 0 or x > 1:
      return np.NaN

  if y < 0 or y > 1:
      return np.NaN

  x = (x*15)-5
  y = y*15

  result = np.square(y - (5.1/(4*np.square(math.pi)))*np.square(x) + (5/math.pi)*x - 6) + 10*(1-(1./(8*math.pi)))*np.cos(x) + 10;

  print 'Result: ', result
  #time.sleep(600)
  return result




# Write a function like this called 'main'
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Returns Branin-Hoo function value at input x and y.')
    parser.add_argument('-x', dest='x',  type=float, help='x coordinate')
    parser.add_argument('-y', dest='y',  type=float, help='y coordinate')
    parser.add_argument('--write-cost-to-file', dest='OUTFILE', default='cost.txt',  help='OUTFILE')

    args = parser.parse_args()
    print 'Args: ', args

    print 'x: ', args.x
    print 'y: ', args.y
    print 'OUTFILE: ', args.OUTFILE
    
    f = open(args.OUTFILE, 'w')
    f.write(str(branin(args.x, args.y)) + '\n')
    f.close()


if __name__ == '__main__':
    main()
