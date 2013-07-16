#!/bin/bash


JOBDIR=$SPEARMINT_JOB_SPOOL_DIR/$(basename $PWD)/job$SPEARMINT_JOB_ID


rm -Rf $JOBDIR 
mkdir -p $JOBDIR  && cd $JOBDIR

pwd

# set up minimal environment
export PATH=$SPEARMINT_JOB_TORCH_PATH:$PATH
export LD_LIBRARY_PATH=$SPEARMINT_JOB_TORCH_LIB_PATH:$LD_LIBRARY_PATH

COMMON_OPTIONS="  -dataset $SPEARMINT_JOB_DATASET -threads $SPEARMINT_JOB_THREADS -maxUpdates $MAX_UPDATES -saveEvery $MAX_UPDATES -visualizeFile -reportEvery $REPORT_EVERY  -train greedy "


# build the deep network

cmd="ae new -dir $JOBDIR/expdir_layer0 -seed $RANDOM -encoder $ENCODER -decoder $DECODER $SPEARMINT_JOB_OPTIONS $COMMON_OPTIONS"

echo $cmd

OMP_NUM_THREADS=$SPEARMINT_JOB_THREADS $cmd


rm -Rf $JOBDIR/reps
cd ..

