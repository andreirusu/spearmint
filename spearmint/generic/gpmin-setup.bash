#!/bin/bash 

### TODO: move to permanent location
export SPEARMINT_HOME=${SPEARMINT_HOME:-"/dmt3/software/spearmint/spearmint"}
export SPEARMINT_THREADS=${SPEARMINT_THREADS:-2}
export SPEARMINT_QUEUE=${SPEARMINT_QUEUE:-"optim.q"}

### SPEARMINT DEFAULT OPTIONS
export GPMIN_MAX_CONCURRENT=${GPMIN_MAX_CONCURRENT:-10}
export GPMIN_MAX_JOBS=${GPMIN_MAX_JOBS:-5000}

export GPMIN_GRID_SEED=$RANDOM


function real_dir_path 
{
    a=`dirname $(readlink -e "$1")`
    b=`basename "$1"`
    echo "$a"/"$b"
}

function print_gpmin_info
{
    echo "Current experiment: "`basename $1`
    echo "Max concurrent jobs: "$GPMIN_MAX_CONCURRENT
    echo "Max total jobs: "$GPMIN_MAX_JOBS
    echo "COMMAND:"
    echo "`cat $1/job.sh`"
}


function print_job_status
{
    JOB_ID=$1
    if [ -z "$JOB_ID" ]
    then
        echo 'STOPPED'
    elif [ -n "`qstat -s r  | grep $JOB_ID - `" ]
    then
        echo 'RUNNING'
    elif [ -n "`qstat -s p  | grep $JOB_ID - `" ]
    then
        echo 'PENDING'
    elif [ -n "`qstat -s s  | grep $JOB_ID - `" ]
    then
        echo 'ERROR'
    else
        echo 'STOPPED'
    fi
}


function gpmin_new 
{
    DATE=$(date +".%Y.%m.%d.%H.%M.%S")
    EXP_DIR=$PWD/gpmin$DATE'.'$GPMIN_GRID_SEED'.'$$ 
    mkdir -p $EXP_DIR   
    # put together a working directory for spearmint 
    cp $1 $EXP_DIR/config.pb
    cp $SPEARMINT_HOME/generic/job.py $EXP_DIR

    ### SET THE COMMAND TO RUN
    SPEARMINT_GPMIN_CMD=${@:2}' $@ ' 

    echo $SPEARMINT_GPMIN_CMD > $EXP_DIR/job.sh
    echo "" > $EXP_DIR/SGE_JOB_ID

    echo $EXP_DIR
}


function gpmin_start  
{
    for EXP_DIR in ${*:1}
    do
        EXP_DIR=`real_dir_path $EXP_DIR`
        if [ ! -d "$EXP_DIR" ] 
        then
            echo "Skipping: \"$EXP_DIR\". Not a valid gpmin directory!"
            continue
        fi

        if [ -f "$EXP_DIR/SGE_JOB_ID" -a -e "$EXP_DIR/SGE_JOB_ID" -a -n "`cat $EXP_DIR/SGE_JOB_ID`" -a -n "$(qstat -s r | grep `cat $EXP_DIR/SGE_JOB_ID` -)" ]
        then
            echo "Skipping: \"$EXP_DIR\". Job not stopped. Please use the restart option!"
            continue
        fi
            
        ## prepare directory for restart
        rm -Rf $EXP_DIR/*lock
        if [ -f "$EXP_DIR/gpmin.log" ]
        then
            cp "$EXP_DIR/gpmin.log"  "$EXP_DIR/gpmin.log.old"
        fi

        ### SCHEDULE SPEARMINT JOB
        echo 'Starting spearmint on SGE...'
        cd $SPEARMINT_HOME

        # get temporary file
        tfile="`mktemp`"

        /dmt3/software/bin/crunch -q $SPEARMINT_QUEUE -o $EXP_DIR/gpmin.log -pe omp.pe $SPEARMINT_THREADS  -V -b y "./spearmint.py --method=GPEIChooser --max-concurrent=$GPMIN_MAX_CONCURRENT --max-finished-jobs=$GPMIN_MAX_JOBS --grid-seed=$GPMIN_GRID_SEED $EXP_DIR " > $tfile  

        cat $tfile | tr -cd [0-9.] |  sed -r 's/^([^.]+).*$/\1/; s/^[^0-9]*([0-9]+).*$/\1/' > $EXP_DIR/SGE_JOB_ID

        cat $tfile
    done
}


function gpmin_stop
{
    for EXP_DIR in ${*:1}
    do 
        EXP_DIR=`real_dir_path $EXP_DIR`
        if [ ! -d "$EXP_DIR" -o ! -f  "$EXP_DIR/SGE_JOB_ID" ]
        then
            echo "Skipping: \"$EXP_DIR\". Not a valid gpmin experiment!"
            continue
        fi
        if [ -d "$EXP_DIR" -a -f "$EXP_DIR/SGE_JOB_ID" -a -n "`cat $EXP_DIR/SGE_JOB_ID`" ]
        then
            echo "EXPERIMENT: `basename $EXP_DIR`"
            JOB_ID="`cat $EXP_DIR/SGE_JOB_ID`"
            # delete job
            qdel $JOB_ID 2>&1 &> /dev/null
            echo "Waiting for job ($JOB_ID) to be deleted..."
            # waiting for job to run
            while [ -n "`qstat  | grep $JOB_ID -`" ] ; 
            do 
                  sleep 0.01
            done
            echo "" > $EXP_DIR/SGE_JOB_ID
        fi 
    done
    echo 'STOPPED'
}

