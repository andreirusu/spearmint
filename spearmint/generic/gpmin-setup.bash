#!/bin/bash -e

### TODO: move to permanent location
export SPEARMINT_HOME=/dmt3/software/spearmint/spearmint
export SPEARMINT_THREADS=2

### SPEARMINT DEFAULT OPTIONS
if [ -z "$GPMIN_MAX_CONCURRENT"  ]
then
    export GPMIN_MAX_CONCURRENT=10
fi

if [ -z "$GPMIN_MAX_JOBS"  ]
then
    export GPMIN_MAX_JOBS=5000
fi

if [ -z "$GPMIN_GRID_SEED"  ]
then
    export GPMIN_GRID_SEED=$RANDOM
fi


function print_gpmin_info
{
    echo "Current experiment: "`basename $1`
    echo "Max concurrent jobs: "$GPMIN_MAX_CONCURRENT
    echo "Max total jobs: "$GPMIN_MAX_JOBS
}



function gpmin_new 
{
    DATE=$(date +".%Y.%m.%d.%H.%M.%S")
    EXP_DIR=$PWD/gpmin$DATE'.'$GPMIN_GRID_SEED'.'$$ 
    mkdir -p $EXP_DIR   
    # put together a working directory for spearmint 
    cp $1 $EXP_DIR/config.pb
    cp $SPEARMINT_HOME/generic/job.py $EXP_DIR
    print_gpmin_info $EXP_DIR

    ### SET THE COMMAND TO RUN
    SPEARMINT_GPMIN_CMD='#!/bin/bash -e 
                        '${@:2}' $@ ' 

    echo "COMMAND: "$SPEARMINT_GPMIN_CMD
    echo $SPEARMINT_GPMIN_CMD > $EXP_DIR/job.sh

    echo $EXP_DIR
}


function gpmin_start  
{
    for EXP_DIR in ${*:1}
    do 
        if [ -d "$dir" -a -f "$dir/SGE_JOB_ID" -a -n "`cat $dir/SGE_JOB_ID`" ]
        then
            ### SCHEDULE SPEARMINT JOB
            echo 'Starting spearmint on SGE...'
            cd $SPEARMINT_HOME

            # get temporary file
            tfile="`mktemp`"

            /dmt3/software/bin/crunch -q torch.q -o $EXP_DIR/gpmin.log -pe omp.pe $SPEARMINT_THREADS  -V -b y "./spearmint.py --method=GPEIChooser --max-concurrent=$GPMIN_MAX_CONCURRENT --max-finished-jobs=$GPMIN_MAX_JOBS --grid-seed=$GPMIN_GRID_SEED $EXP_DIR " > $tfile

            cat $tfile | tr -cd [0-9.] |  sed -r 's/^([^.]+).*$/\1/; s/^[^0-9]*([0-9]+).*$/\1/' > $EXP_DIR/SGE_JOB_ID

            cat $tfile
        fi
    done
}


function gpmin_stop
{
    for dir in ${*:1}
    do 
        if [ -d "$dir" -a -f "$dir/SGE_JOB_ID" -a -n "`cat $dir/SGE_JOB_ID`" ]
        then
            echo "EXPERIMENT: `basename $dir`"
            JOB_ID="`cat $dir/SGE_JOB_ID`"
            # delete job
            qdel $JOB_ID 2>&1 &> /dev/null
            echo "Waiting for job ($JOB_ID) to be deleted..."
            # waiting for job to run
            while [ -n "`qstat  | grep $JOB_ID -`" ] ; 
            do 
                  sleep 0.01
            done
        fi 
    done
}

