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
    setEnvVar(env, 'SPEARMINT_JOB_TORCH_PATH', '/dmt/software/bin:/Users/andreirusu/.torch/usr/bin')
    setEnvVar(env, 'SPEARMINT_JOB_TORCH_LIB_PATH', '/dmt/software/lib')
    # set up job
    setEnvVar(env, 'SPEARMINT_JOB_ID', job_id)
    setEnvVar(env, 'SPEARMINT_JOB_THEREADS', 2)
    setEnvVar(env, 'SPEARMINT_JOB_DATASET', '/Users/andreirusu/projects/experiment-utils/examples/datasets/mnist')
    setEnvVar(env, 'SPEARMINT_JOB_SPOOL_DIR', '/data/andrei/jobdirs')
    setEnvVar(env, 'SPEARMINT_JOB_TEST_OPTIONS', ' -l 50000 -s 5 ')
    # XAE PARAMETERS
    setEnvVar(env, 'ENCODER', 'rlu')
    setEnvVar(env, 'DECODER', 'linear')
    setEnvVar(env, 'MAX_UPDATES', 1e5)
    setEnvVar(env, 'REPORT_EVERY', 49999)
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER0', appendAllCommandLineOptions(params, 0))
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER1', appendAllCommandLineOptions(params, 1))
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER2', appendAllCommandLineOptions(params, 2))

        
    # call job
    cmd = ['bash', 'job.sh']
    try:
        p = sp.Popen(cmd, env=env)
        p.wait()
    except:
        print(sys.exc_info())
    
    # read back result
    f = open(os.path.join(env['SPEARMINT_JOB_SPOOL_DIR'], os.path.basename(os.getcwd()), 'job' + str(job_id), 'res.txt'))
    lines = f.readlines()
    print(lines[3])
    # optimizer tries to minimize error, so report error, NOT accuracy
    result = 100 - float(lines[3].split(': ')[1])
    print(result)
    print('Success!')
    return result
        

def main(job_id, params):
    print 'Anything printed here will end up in the output directory of job #:', str(job_id)
    print params
    return job(job_id, params)


if __name__ == '__main__' :
    params = {}
    params['learningRate'] = [0.1, 0.1, 0.1]
    params['momentum'] = [0.9, 0.9, 0.9]
    params['hidden'] = [1000, 1000, 1000]
    params['dropoutRatio'] = [0.3, 0.5, 0.5]
    params['L1Cost'] = [0.1, 0.1, 0.1]
    main(12345, params)

