import os
import sys
import math
import time

import numpy as np
import subprocess as sp


def setEnvVar(env, varName, value):
    env[str(varName)] = str(value)


def appendCommandLineOption(original, optionStr, params, ind):
    return original + ' -' + optionStr + ' ' + str(params[optionStr][ind]) + ' '


def appendAllCommandLineOptions(params, ind):
    options = ''
    # iterate over all parameters at a certain index
    for option in params:
        options = appendCommandLineOption(options, option, params, ind) 
    return options


def job(job_id, params):
    # set the environment
    env = os.environ
    # set up minimal environment
    setEnvVar(env, 'SGE_ROOT', '/var/lib/gridengine')
    # set up job
    setEnvVar(env, 'OMP_NUM_THREADS', 1)
    # ADD JOB PARAMETERS
    outfilename = os.path.join('output', 'cost.' + env['JOB_ID'] + '.txt')
    commandStr = appendAllCommandLineOptions(params, 0) + ' --write-cost-to-file ' + outfilename
   
    # call job
    import shlex
    args = shlex.split('/bin/bash ' +  os.path.join(os.getcwd(), 'job.sh') + commandStr)
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

