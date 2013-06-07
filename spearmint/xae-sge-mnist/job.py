import numpy as np
import subprocess as sp
import os
import sys
import math
import time


def setEnvVar(env, varName, value):
    env[str(varName)] = str(value)


def appendCommandLineOption(original, optionStr, params, ind):
    return original + ' -' + optionStr + ' ' + str(params[optionStr][ind]) + ' '


def appendAllCommandLineOptions(params, ind):
    options = ''
    # iterate over all parameters at a certain index
    for option in params:
        options = options + appendCommandLineOption(options, option, params, ind) 
    return options


def job(job_id, params):
    # set the environment
    env = os.environ
    setEnvVar(env, 'SPEARMINT_JOB_ID', job_id)
    setEnvVar(env, 'SPEARMINT_JOB_THEREADS', 2)
    setEnvVar(env, 'DATASET', '/Users/andreirusu/projects/experiment-utils/examples/datasets/mnist')
    setEnvVar(env, 'SPOOL_DIR', '/data/andrei/jobdirs')
    setEnvVar(env, 'SPEARMINT_JOB_TEST_OPTIONS', ' -l 50000 -s 5 ')
    # XAE PARAMETERS
    setEnvVar(env, 'ENCODER', 'logistic')
    setEnvVar(env, 'DECODER', 'logistic')
    setEnvVar(env, 'MAX_UPDATES', 1e3)
    setEnvVar(env, 'REPORT_EVERY', 499)
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER0', appendAllCommandLineOptions(params, 0))
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER1', appendAllCommandLineOptions(params, 1))
    setEnvVar(env, 'SPEARMINT_JOB_OPTIONS_LAYER2', appendAllCommandLineOptions(params, 2))

        
    # call job
    cmd = ['sh', 'job.sh']
    try:
        p = sp.Popen(cmd, env=env)
        p.wait()
    except:
        print(sys.exc_info())
    
    print('Success!')

	# read back result
	f = open('/data/andrei/jobdirs/xae-sge-mnist/job'+str(job_id)+'/res.txt')
	lines = f.readlines()
	print(lines[3])
	result = float(lines[3].split(': ')[1])
	print(result)
	# optimizer tries to minimize error, so report error, NOT accuracy
	return (100.0 - result)
	

def main(job_id, params):
    print 'Anything printed here will end up in the output directory of job #:', str(job_id)
    print params
    return job(job_id, params)


if __name__ == '__main__' :
    params = {}
    params['learningRate'] = [0.1, 0.1, 0.1]
    params['momentum'] = [0.9, 0.9, 0.9]
    params['hidden'] = [500, 100, 50]
    params['dropoutRatio'] = [0.3, 0.5, 0.5]
    params['L1Cost'] = [0.1, 0.1, 0.1]
    main(12345, params)

