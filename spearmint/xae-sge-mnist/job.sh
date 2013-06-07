#!/bin/bash

export OMP_NUM_THREADS=$SPEARMINT_JOB_THEREADS

DATASET_SUP=$DATASET

JOBDIR=$SPOOL_DIR/$(basename $PWD)/job$SPEARMINT_JOB_ID


rm -Rf $JOBDIR 
mkdir -p $JOBDIR  && cd $JOBDIR

pwd

# set up minimal environment
export SGE_ROOT=/var/lib/gridengine/
export PATH=/dmt3/software/bin:/Users/andreirusu/.torch/usr/bin:$PATH
export LD_LIBRARY_PATH=/dmt3/software/lib:$LD_LIBRARY_PATH

COMMON_OPTIONS="  -dataset $DATASET -threads $SPEARMINT_JOB_THEREADS -maxUpdates $MAX_UPDATES -saveEvery $MAX_UPDATES -visualizeFile -reportEvery $REPORT_EVERY  -train greedy "


# build the deep network

ae new -dir $JOBDIR/expdir_layer0  -encoder $ENCODER -decoder linear $SPEARMINT_JOB_OPTIONS_LAYER0 $COMMON_OPTIONS 

ae stack $JOBDIR/expdir_layer0 -dir $JOBDIR/expdir_layer1 -encoder $ENCODER -decoder $DECODER $SPEARMINT_JOB_OPTIONS_LAYER1 $COMMON_OPTIONS 

ae stack $JOBDIR/expdir_layer1 -dir $JOBDIR/expdir_layer2 -encoder $ENCODER -decoder $DECODER $SPEARMINT_JOB_OPTIONS_LAYER2 $COMMON_OPTIONS 

ae-export-features -input $JOBDIR/expdir_layer2 -format tensor -output $JOBDIR/reps/last -dataset $DATASET_SUP

ae-svm-test -r $JOBDIR/reps -f $JOBDIR/res.txt $SPEARMINT_JOB_TEST_OPTIONS

rm -Rf $JOBDIR/reps
cd ..

