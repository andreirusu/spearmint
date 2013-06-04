##
# Copyright (C) 2012 Jasper Snoek, Hugo Larochelle and Ryan P. Adams
#                                                                                                                                                                              
# This code is written for research and educational purposes only to
# supplement the paper entitled "Practical Bayesian Optimization of
# Machine Learning Algorithms" by Snoek, Larochelle and Adams Advances
# in Neural Information Processing Systems, 2012
#                                                                                                                                                       
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#                                                                                                                                                                       
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#                                                                                                                                                                       
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
import optparse
import tempfile
import datetime
import subprocess
import time
import imp
import os
import re
import collections

import matplotlib as plt
import matplotlib.pyplot as pplt

from ExperimentGrid  import *
try: import simplejson as json
except ImportError: import json

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

def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] directory")

    parser.add_option("--method", dest="chooser_module",
                      help="Method for choosing experiments.",
                      type="string", default="GPEIOptChooser")
    parser.add_option("--method-args", dest="chooser_args",
                      help="Arguments to pass to chooser module.",
                      type="string", default="")
    parser.add_option("--config", dest="config_file",
                      help="Configuration file name.",
                      type="string", default="config.json")
    parser.add_option("--grid-size", dest="grid_size",
                      help="Grid size on each plotting dimension.",
                      type="string", default=100)
    parser.add_option("--results", dest="results_file",
                      help="Results file name.",
                      type="string", default="results.dat")
    parser.add_option("--plot-dir", dest="plot_dir",
                      help="Directory to store plots.",
                      type="string", default="plots")

    (options, args) = parser.parse_args()

    # Otherwise run in controller mode.
    main_controller(options, args)

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
    pplt.ylabel(r'$f')
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


def evaluate_gp(chooser, candidates, complete, values, durations, pending):
    # Ask the choose to compute the GP on this grid
    # First mash the data into a format that matches that of the other
    # spearmint drivers to pass to the chooser modules.        
    grid = candidates
    if (complete.shape[0] > 0):
        grid = np.vstack((complete, candidates))
    if (pending.shape[0] > 0):
        grid = np.vstack((grid, pending))
    grid = np.asarray(grid)
    grid_idx = np.hstack((np.zeros(complete.shape[0]),
                          np.ones(candidates.shape[0]),
                          1.+np.ones(pending.shape[0])))

    mean, variance = chooser.plot(grid, np.squeeze(values), durations,
                         np.nonzero(grid_idx == 1)[0],
                         np.nonzero(grid_idx == 2)[0],
                         np.nonzero(grid_idx == 0)[0])
    return (mean, variance)

def read_results(res_file, gmap):
    values = np.array([])
    complete = np.array([])
    pending = np.array([])
    durations = np.array([])

    infile = open(res_file, 'r')
    for line in infile.readlines():
        # Each line in this file represents an experiment
        # It is whitespace separated and of the form either
        # <Value> <time taken> <space separated list of parameters>
        # incating a completed experiment or
        # P P <space separated list of parameters>
        # indicating a pending experiment
        expt = line.split()
        if (len(expt) < 3):
            continue

        val = expt.pop(0)
        dur = expt.pop(0)
        variables = gmap.to_unit(expt)
        if val == 'P':
            if pending.shape[0] > 0:
                pending = np.vstack((pending, variables))
            else:
                pending = np.matrix(variables)
        else:
            if complete.shape[0] > 0:
                values = np.vstack((values, float(val)))
                complete = np.vstack((complete, variables))
                durations = np.vstack((durations, float(dur)))
            else:
                values = float(val)
                complete = np.matrix(variables)
                durations = float(dur)

    infile.close()
    # Some stats
    sys.stderr.write("#Complete: %d #Pending: %d\n" % 
                     (complete.shape[0], pending.shape[0]))

    return (values, complete, pending, durations)

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
        params = gmap.unit_to_list(candidates[i,:])
        for p in params:
            output = output + str(p) + ","
        output = output + str(mean[i]) + "," + str(variance[i]) + "\n"

    out = open(csv_file,"w")
    out.write(output)
    out.close()


##############################################################################
##############################################################################
def main_controller(options, args):

    expt_dir  = os.path.realpath(args[0])
    work_dir  = os.path.realpath('.')
    expt_name = os.path.basename(expt_dir)

    if not os.path.exists(expt_dir):
        sys.stderr.write("Cannot find experiment directory '%s'.  Aborting.\n" % (expt_dir))
        sys.exit(-1)

    plot_dir = os.path.join(expt_dir, options.plot_dir)
    if not os.path.exists(plot_dir):
        sys.stderr.write("Creating plot directory '%s'.\n" % (plot_dir))
        os.mkdir(plot_dir)

    # Load up the chooser module.
    module  = __import__(options.chooser_module)
    chooser = module.init(expt_dir, options.chooser_args)

    # Create the experimental grid
    expt_file = os.path.join(expt_dir, options.config_file)
    variables = json.load(open(expt_file), object_pairs_hook=collections.OrderedDict)

    #@gdahl - added the following three lines and commented out the line above
    vkeys = [k for k in variables]
    #vkeys.sort()
    gmap = GridMap([variables[k] for k in vkeys], 1)

    res_file = os.path.join(expt_dir, options.results_file)
    if not os.path.exists(res_file):
        thefile = open(res_file, 'w')
        thefile.write("")
        thefile.close()

    # Read results from file
    values, complete, pending, durations = read_results(res_file, gmap)

    # Let's print out the best value so far
    if type(values) is not float and len(values) > 0:
        best_val = np.min(values)
        best_job = np.argmin(values)
        sys.stderr.write("Current best: %f (job %d)\n" % (best_val, best_job))
        best_complete = complete[best_job,:]
    else:
        # TODO: deal with plotting the prior GP with no evaluated points
        sys.stderr.write("Need at least one complete evaluation to plot\n")
        sys.exit(-1)

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
                                       candidates, complete, values,
                                       durations, pending)
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
                                                   candidates, complete, values,
                                                   durations, pending)
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

# And that's it
if __name__ == '__main__':
    main()
