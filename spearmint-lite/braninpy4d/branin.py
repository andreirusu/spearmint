import numpy as np
import sys
import math
import time

def branin(x, y):
  x[0] = (x[0]*15)-5
  x[1] = x[1]*15

  y[0] = (y[0]*15)-5
  y[1] = y[1]*15

  zx = np.square(x[1] - (5.1/(4*np.square(math.pi)))*np.square(x[0]) + (5/math.pi)*x[0] - 6) + 10*(1-(1./(8*math.pi)))*np.cos(x[0]) + 10;

  zy = np.square(y[1] - (5.1/(4*np.square(math.pi)))*np.square(y[0]) + (5/math.pi)*y[0] - 6) + 10*(1-(1./(8*math.pi)))*np.cos(y[0]) + 10;

  result = zx * zy;
  #time.sleep(5)

  return result

# Write a function like this called 'main'
def main(job_id, params):
  return branin(params['X'])
