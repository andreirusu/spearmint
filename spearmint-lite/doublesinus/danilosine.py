import numpy as np
import sys
import math
import time

def danilosine(x):

  result = x + .3*np.sin(x*2*math.pi) + .3*np.sin(4*math.pi*x)
  return result

# Write a function like this called 'main'
def main(job_id, params):
  return danilosine(params['X'])
