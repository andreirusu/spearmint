##
# Copyright (C) 2012 Jasper Snoek, Hugo Larochelle and Ryan P. Adams
# 
# This code is written for research and educational purposes only to 
# supplement the paper entitled
# "Practical Bayesian Optimization of Machine Learning Algorithms"
# by Snoek, Larochelle and Adams
# Advances in Neural Information Processing Systems, 2012
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import optparse
import tempfile
import datetime
import subprocess
import time
import imp
import os
import re

from google.protobuf import text_format
from spearmint_pb2   import *
from ExperimentGrid  import *

import matplotlib as plt
import matplotlib.pyplot as pplt

DEFAULT_MODULES = [ 'packages/epd/7.1-2',
                    'packages/matlab/r2011b',
                    'mpi/openmpi/1.2.8/intel',
                    'libraries/mkl/10.0',
                    'packages/cuda/4.0',
                    ]
MCR_LOCATION = "/home/matlab/v715" # hack

#
# There are two things going on here.  There are "experiments", which are
# large-scale things that live in a directory and in this case correspond
# to the task of minimizing a complicated function.  These experiments
# contain "jobs" which are individual function evaluations.  The set of
# all possible jobs, regardless of whether they have been run or not, is
# the "grid".  This grid is managed by an instance of the class
# ExperimentGrid.
#
# The spearmint.py script can run in two modes, which reflect experiments
# vs jobs.  When run with the --wrapper argument, it will try to run a
# single job.  This is not meant to be run by hand, but is intended to be
# run by a job queueing system.  Without this argument, it runs in its main
# controller mode, which determines the jobs that should be executed and
# submits them to the queueing system.
#



################# START ### ANDREI ########################

# Compute a grid on the 1D slice containing
# point v and along dimensions dim
def slice_1d(v, dim, grid_size):
    vrep = v.repeat(grid_size, 0)

    left = vrep[:, 0:dim].reshape(grid_size, dim)
    print('left is ' + str(left.shape))
    right = vrep[:, dim+1:].reshape(grid_size, v.shape[1]-dim-1)
    print('right is ' + str(right.shape))

    x = np.linspace(0, 1, grid_size).reshape(grid_size, 1)
    print('x is ' + str(x.shape))

    return (x, np.hstack((left, x, right)))

def plot_1d(x, mean, variance, slice_at, var_name):
    pplt.figure()
    h_mean, = pplt.plot(x, mean)
    h_bound, = pplt.plot(x, mean+np.sqrt(variance), 'r--')
    pplt.plot(x, mean-np.sqrt(variance), 'r--')
    pplt.xlabel(r'$' + var_name + '$')
    pplt.ylabel(r'$f$')
    slice_at_list = np.squeeze(np.asarray(slice_at)).tolist()
    slice_at_string = str(["%.2f" % member for member in slice_at_list])
    pplt.title(r'Slice along ' + var_name + ' at ' + slice_at_string) #+ str(slice_at.tolist()))
    pplt.legend([h_mean, h_bound],
                ["Mean", "+/- Standard dev."],
                loc="upper right")
    pplt.draw()


# Compute a grid on the 1D slice containing
# and along dimensions  dim1 and dim2
def slice_2d(v, dim1, dim2, side_size):
    square_size = side_size * side_size

    vrep = v.repeat(square_size, 0)

    left = vrep[:, 0:dim1].reshape(square_size, dim1)
    middle = vrep[:, dim1+1:dim2].reshape(square_size, dim2-(dim1+1))
    right = vrep[:, dim2+1:].reshape(square_size, v.shape[1]-(dim2+1))

    x = np.linspace(0, 1, side_size)
    y = np.linspace(0, 1, side_size)

    xx, yy = np.meshgrid(x, y)
    xxcol = xx.reshape(square_size, 1)
    yycol = yy.reshape(square_size, 1)

    return (x, y, np.hstack((left, xxcol, middle, yycol, right)))

def plot_2d(x, y, mean, variance, slice_at, v1_name, v2_name):
    pplt.figure()
    pplt.subplot(121)
    h_mean = pplt.pcolormesh(x, y, 
                             mean.reshape(x.shape[0], y.shape[0]))
    pplt.colorbar(h_mean)
    slice_at_list = np.squeeze(np.asarray(slice_at)).tolist()
    slice_at_string = str(["%.2f" % member for member in slice_at_list])
    pplt.xlabel(r'$' + v1_name + '$')
    pplt.ylabel(r'$' + v2_name + '$')
    pplt.title(r'Mean, slice along $( ' + v1_name + ',' + v2_name + ')$ at ' +
               slice_at_string)

    pplt.subplot(122)
    h_var = pplt.pcolormesh(x, y, variance.reshape(x.shape[0],
                                                   y.shape[0]))
    pplt.colorbar(h_var)
    pplt.xlabel(r'$' + v1_name + '$')
    pplt.ylabel(r'$' + v2_name + '$')
    pplt.title(r'Variance, slice along $( ' + v1_name + ',' + v2_name + ')$ at ' +
               slice_at_string)
    pplt.draw()


def evaluate_gp(chooser, candidates, complete, values, durations):
    # Ask the choose to compute the GP on this grid
    # First mash the data into a format that matches that of the other
    # spearmint drivers to pass to the chooser modules.        
    grid = candidates
    if (complete.shape[0] > 0):
        grid = np.vstack((complete, candidates))
    grid = np.asarray(grid)
    grid_idx = np.hstack((np.zeros(complete.shape[0]),
                          np.ones(candidates.shape[0])))
    print('candidates is' + str(candidates))
    print('complete is' + str(complete))
    print('values is' + str(values))

    mean, variance = chooser.plot(grid, np.squeeze(values), durations,
                         np.nonzero(grid_idx == 1)[0],
                         np.nonzero(grid_idx == 2)[0],
                         np.nonzero(grid_idx == 0)[0])
    return (mean, variance)

def save_to_csv(csv_file, gmap, candidates, mean, variance):
    # Now lets write this evaluation to the CSV plot file
    output = ""
    for v in gmap.variables:
        dim = v['size']
        if dim > 1:
            for i in range(1,dim+1):
                output = output + str(v['name']) + "_" + str(i) + ","
        else:
            output = output + str(v['name']) + ","

    output = output + "Mean,Variance\n"

    candidates = np.asarray(candidates)
    for i in range(0,candidates.shape[0]):
        for p in candidates[i,:]:
            output = output + str(p) + ","
        output = output + str(mean[i]) + "," + str(variance[i]) + "\n"

    out = open(csv_file,"w")
    out.write(output)
    out.close()



################# END ### ANDREI ########################






def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] directory")

    parser.add_option("--max-concurrent", dest="max_concurrent",
                      help="Maximum number of concurrent jobs.",
                      type="int", default=1)
    parser.add_option("--max-finished-jobs", dest="max_finished_jobs",
                      type="int", default=1000)
    parser.add_option("--method", dest="chooser_module",
                      help="Method for choosing experiments.",
                      type="string", default="GPEIChooser")
    parser.add_option("--method-args", dest="chooser_args",
                      help="Arguments to pass to chooser module.",
                      type="string", default="")
    parser.add_option("--grid-size", dest="grid_size",
                      help="Number of points in each dimension of the plotting grid.",
                      type="int", default=100)
    parser.add_option("--grid-seed", dest="grid_seed",
                      help="The seed used to initialize initial grid.",
                      type="int", default=1)
    parser.add_option("--config", dest="config_file",
                      help="Configuration file name.",
                      type="string", default="config.pb")
    parser.add_option("--wrapper", dest="wrapper",
                      help="Run in job-wrapper mode.",
                      action="store_true")
    parser.add_option("--plot-dir", dest="plot_dir",
                      help="Directory to store plots.",
                      type="string", default="plots")

    (options, args) = parser.parse_args()

    if options.wrapper:
        # Possibly run in job wrapper mode.
        main_wrapper(options, args)

    else:
        # Otherwise run in controller mode.
        main_controller(options, args)
    
##############################################################################
##############################################################################
def main_wrapper(options, args):
    sys.stderr.write("Running in wrapper mode for '%s'\n" % (args[0]))

    # This happens when the job is actually executing.  Now we are
    # going to do a little bookkeeping and then spin off the actual
    # job that does whatever it is we're trying to achieve.

    # Load in the Protocol buffer spec for this job and experiment.
    job_file = args[0]
    job      = load_job(job_file)

    ExperimentGrid.job_running(job.expt_dir, job.id)
    
    # Update metadata.
    job.start_t = int(time.time())
    job.status  = 'running'
    save_job(job_file, job)

    ##########################################################################
    success    = False
    start_time = time.time()

    try:
        if job.language == MATLAB:
            # Run it as a Matlab function.
            function_call = "matlab_wrapper('%s'), quit;" % (job_file)
            matlab_cmd    = 'matlab -nosplash -nodesktop -r "%s"' % (function_call)
            sys.stderr.write(matlab_cmd + "\n")
            os.system(matlab_cmd)

        elif job.language == PYTHON:
            # Run a Python function
            sys.stderr.write("Running python job.\n")

            # Add directory to the system path.
            sys.path.append(os.path.realpath(job.expt_dir))

            # Change into the directory.
            os.chdir(job.expt_dir)
            sys.stderr.write("Changed into dir %s\n" % (os.getcwd()))

            # Convert the PB object into useful parameters.
            params = {}
            for param in job.param:
                dbl_vals = param.dbl_val._values
                int_vals = param.int_val._values
                str_vals = param.str_val._values

                if len(dbl_vals) > 0:
                    params[param.name] = np.array(dbl_vals)
                elif len(int_vals) > 0:
                    params[param.name] = np.array(int_vals, dtype=int)
                elif len(str_vals) > 0:
                    params[param.name] = str_vals
                else:
                    raise Exception("Unknown parameter type.")

            # Load up this module and run
            module  = __import__(job.name)
            result = module.main(job.id, params)

            sys.stderr.write("Got result %f\n" % (result))

            # Change back out.
            os.chdir('..')

            # Store the result.
            job.value = result
            save_job(job_file, job)

        elif job.language == SHELL:
            # Change into the directory.
            os.chdir(job.expt_dir)

            cmd = './%s %s' % (job.name, job_file)
            sys.stderr.write("Executing command '%s'\n" % (cmd))

            os.system(cmd)

        elif job.language == MCR:

            # Change into the directory.
            os.chdir(job.expt_dir)

            if os.environ.has_key('MATLAB'):
                mcr_loc = os.environ['MATLAB']
            else:
                mcr_loc = MCR_LOCATION

            cmd = './run_%s.sh %s %s' % (job.name, mcr_loc, job_file)
            sys.stderr.write("Executing command '%s'\n" % (cmd))
            os.system(cmd)

        else:
            raise Exception("That function type has not been implemented.")

        success = True
    except:
        sys.stderr.write("Problem executing the function\n")
        print sys.exc_info()
        
    end_time = time.time()
    duration = end_time - start_time
    ##########################################################################

    job = load_job(job_file)
    sys.stderr.write("Job file reloaded.\n")

    if not job.HasField("value"):
        sys.stderr.write("Could not find value in output file.\n")
        success = False

    if success:
        sys.stderr.write("Completed successfully in %0.2f seconds. [%f]\n" 
                         % (duration, job.value))

        # Update the status for this job.
        ExperimentGrid.job_complete(job.expt_dir, job.id,
                                    job.value, duration)
    
        # Update metadata.
        job.end_t    = int(time.time())
        job.status   = 'complete'
        job.duration = duration

    else:
        sys.stderr.write("Job failed in %0.2f seconds.\n" % (duration))

        # Update the status for this job.
        ExperimentGrid.job_broken(job.expt_dir, job.id)
    
        # Update metadata.
        job.end_t    = int(time.time())
        job.status   = 'broken'
        job.duration = duration

    save_job(job_file, job)

##############################################################################
##############################################################################
def main_controller(options, args):

    expt_dir  = os.path.realpath(args[0])
    work_dir  = os.path.realpath('.')
    expt_name = os.path.basename(expt_dir)

    if not os.path.exists(expt_dir):
        sys.stderr.write("Cannot find experiment directory '%s'.  Aborting.\n" % (expt_dir))
        sys.exit(-1)

    # Load up the chooser module.
    module  = __import__(options.chooser_module)
    chooser = module.init(expt_dir, options.chooser_args)
 
    # Loop until we run out of jobs.
    attempt_dispatch(expt_name, expt_dir, work_dir, chooser, options)
 
def attempt_dispatch(expt_name, expt_dir, work_dir, chooser, options):
    #import drmaa

    sys.stderr.write("\n")
    
    expt_file = os.path.join(expt_dir, options.config_file)
    expt      = load_expt(expt_file)

    # Build the experiment grid.
    expt_grid = ExperimentGrid(expt_dir,
                               expt.variable,
                               options.grid_size,
                               options.grid_seed)

    # Print out the current best function value.
    best_val, best_job = expt_grid.get_best()
    sys.stderr.write("Current best: %f (job %d)\n" % (best_val, best_job))
 
    # Gets you everything - NaN for unknown values & durations.
    grid, values, durations = expt_grid.get_grid()
    
    # Returns lists of indices.
    candidates = expt_grid.get_candidates()
    pending    = expt_grid.get_pending()
    complete   = expt_grid.get_complete()
    sys.stderr.write("%d candidates   %d pending   %d complete\n" % 
                     (candidates.shape[0], pending.shape[0], complete.shape[0]))

    ################# START ### ANDREI ########################
    plot_dir = os.path.join(expt_dir, options.plot_dir)
    if not os.path.exists(plot_dir):
        sys.stderr.write("Creating plot directory '%s'.\n" % (plot_dir))
        os.mkdir(plot_dir)
     
    gmap = expt_grid.vmap

    if np.isnan(best_job):
        # TODO: deal with plotting the prior GP with no evaluated points
        sys.stderr.write("Need at least one complete evaluation to plot\n")
        sys.exit(-1)
    best_complete = grid[best_job, :].reshape((1,gmap.cardinality))

    print('Best complete is ' + str(best_complete))
    print('best_complete.shape is ' + str(best_complete.shape))

    # Loop on first dimension
    grid_i = 0
    for v1 in gmap.variables:
        v1_dim = v1['size']
        for i in range(0,v1_dim):
            v1_name = str(v1['name'])
            if v1_dim > 1:
                v1_name = v1_name + "_" + str(i+1)

            # Evaluate on the marginal slice containing the best fit
            print('slicing along dim ' + str(grid_i))
            x, candidates = slice_1d(best_complete, grid_i, options.grid_size)
            mean, variance = evaluate_gp(chooser, 
                    candidates, grid[complete, :], values[complete],
                    durations[complete])
            plot_1d(x, mean, variance, best_complete, v1_name)
            pplt.savefig(os.path.join(plot_dir, v1_name + '.png'))
            out_file = os.path.join(plot_dir, v1_name + '.csv')
            save_to_csv(out_file, gmap, candidates, mean, variance)

            # Loop on second dimension
            grid_j = 0
            for v2 in gmap.variables:
                v2_dim = v2['size']
                for j in range(0,v2_dim):
                    # Sub-diagonal is skipped
                    if grid_j <= grid_i:
                        grid_j = grid_j + 1
                        continue

                    v2_name = str(v2['name'])
                    if v2_dim > 1:
                        v2_name = v2_name + "_" + str(j+1)

                    # Now let's evaluate the GP on a grid
                    x, y, candidates = slice_2d(best_complete, grid_i, grid_j, options.grid_size)
                    mean, variance = evaluate_gp(chooser, 
                            candidates, grid[complete, :], values[complete],
                            durations[complete])
                    plot_2d(x, y, mean, variance, best_complete, v1_name,
                            v2_name)
                    pplt.savefig(os.path.join(plot_dir, 
                                              v1_name + "_" + v2_name + ".png"))
                    out_file = os.path.join(plot_dir,
                                              v1_name + "_" + v2_name + ".csv")
                    save_to_csv(out_file, gmap, candidates, mean, variance)
                    grid_j = grid_j + 1

            grid_i = grid_i + 1

    pplt.show()
    ################# END ### ANDREI ########################
    
    
def load_expt(filename):
    fh = open(filename, 'rb')
    expt = Experiment()
    text_format.Merge(fh.read(), expt)
    fh.close()
    return expt

def load_job(filename):
    fh = open(filename, 'rb')
    job = Job()
    #text_format.Merge(fh.read(), job)
    job.ParseFromString(fh.read())
    fh.close()
    return job

def save_expt(filename, expt):
    fh = tempfile.NamedTemporaryFile(mode='w', delete=False)
    fh.write(text_format.MessageToString(expt))
    fh.close()
    cmd = 'mv "%s" "%s"' % (fh.name, filename)
    os.system(cmd)

def save_job(filename, job):
    fh = tempfile.NamedTemporaryFile(mode='w', delete=False)
    #fh.write(text_format.MessageToString(job))
    fh.write(job.SerializeToString())
    fh.close()
    cmd = 'mv "%s" "%s"' % (fh.name, filename)
    os.system(cmd)

def sge_submit(name, output_file, modules, job_file, working_dir):

    sge_script = '''
#!/bin/bash
#$ -S /bin/bash
#$ -N "%s"
#$ -j yes
#$ -e "%s"
#$ -o "%s"
#$ -wd "%s"
#$ -q torch.q
#$ -cwd

# Set up the environment
. /etc/profile
. ~/.profile

# Make sure we have various modules.
# module load %s

# Spin off ourselves as a wrapper script.
exec python2.7 spearmint.py --wrapper "%s"

''' % (name, output_file, output_file, working_dir, " ".join(modules), job_file)

    # Submit the job.
    process = subprocess.Popen('qsub',
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               shell=False)
    output = process.communicate(input=sge_script)[0]
    process.stdin.close()

    # Parse out the job id.
    match = re.search(r'Your job (\d+)', output)
    if match:
        return int(match.group(1)), output
    else:
        return None, output

if __name__ == '__main__':
    main()
