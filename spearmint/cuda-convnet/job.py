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
    setEnvVar(env, 'MKL_NUM_THREADS', 1)
    setEnvVar(env, 'EXP_DIR', os.getcwd())
    setEnvVar(env, 'SPEARMINT_JOB_ID', job_id)
    # ADD JOB PARAMETERS
    outdir = os.path.join(env['EXP_DIR'], 'jobdirs', str(job_id))
    try:
        os.makedirs(outdir)
    except:
        pass
    outfilename = os.path.join(outdir, 'cost.' + str(job_id)  + '.txt')
    setEnvVar(env, 'cost_out_filename', outfilename)
    setAllEnvVar(env, params, 0) 
    # call job
    import shlex
    args = shlex.split('/bin/bash /dmt3/software/bin/withgpu ' +  os.path.join(env['EXP_DIR'], 'job.sh'))
    try:
        p = sp.Popen(args, env=env, cwd=outdir)
        p.wait()
    except:
        print(sys.exc_info())
    # read back result
    f = open(outfilename)
    lines = f.readlines()
    # optimizer tries to minimize error
    result = float(lines[0])
    print(result)
    print('Success!')
    return result
        

def main(job_id, params):
    print 'Anything printed here will end up in the output directory of job #:', str(job_id)
    print params
    return job(job_id, params)

