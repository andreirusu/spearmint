import os
import sys
import math
import time

import numpy as np
import subprocess as sp


def setEnvVar(env, varName, value):
    env[str(varName)] = str(value)


def setAllEnvVar(env, params, ind):
    for option in params:
        setEnvVar(env, option, params[option][ind]) 
 

def job(job_id, params):
    # set the environment
    env = os.environ
    # set up minimal environment
    setEnvVar(env, 'SGE_ROOT', '/var/lib/gridengine')
    # set up job
    setEnvVar(env, 'OMP_NUM_THREADS', 1)
    # ADD JOB PARAMETERS
    outfilename = os.path.join(os.getcwd(), 'output', 'cost.' + str(job_id)  + '.txt')
    setEnvVar(env, 'cost_out_filename', outfilename)
    setAllEnvVar(env, params, 0) 
   
    # call job
    import shlex
    args = shlex.split('/bin/bash /dmt3/software/bin/withgpu ' +  os.path.join(os.getcwd(), 'job.sh'))
    print(env)
    print(args)
    try:
        p = sp.Popen(args, env=env)
        #p = sp.Popen(args, env=env, cwd=env['SGE_JOB_SPOOL_DIR'])
        p.wait()
    except:
        print(sys.exc_info())
    
    # read back result
    print(os.getcwd())
    f = open(outfilename)
    #f = open(os.path.join(env['SGE_JOB_SPOOL_DIR'], outfilename))
    lines = f.readlines()
    print(lines[0])
    # optimizer tries to minimize error
    result = float(lines[0])
    print(result)
    print('Success!')
    return result
        

def main(job_id, params):
    print 'Anything printed here will end up in the output directory of job #:', str(job_id)
    print params
    return job(job_id, params)


if __name__ == '__main__':
    d={}
    d['cost_out_filename'] = ['cost.txt']
    main(1234, d)


