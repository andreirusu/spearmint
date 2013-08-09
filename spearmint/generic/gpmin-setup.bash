#!/bin/bash  


function set_env
{
    ### TODO: move to permanent location
    SPEARMINT_HOME=${SPEARMINT_HOME:-"/dmt3/software/spearmint/spearmint"}
    SPEARMINT_THREADS=${SPEARMINT_THREADS:-2}
    SPEARMINT_QUEUE=${SPEARMINT_QUEUE:-"med.q"}
    SPEARMINT_METHOD=${SPEARMINT_METHOD:-"GPEIOptChooser"}

    ### SPEARMINT DEFAULT OPTIONS
    GPMIN_MAX_CONCURRENT=${GPMIN_MAX_CONCURRENT:-10}
    GPMIN_MAX_JOBS=${GPMIN_MAX_JOBS:-500}
    GPMIN_RESTARTS=${GPMIN_RESTARTS:-5}

    GPMIN_GRID_SEED=$RANDOM
}

function set_args
{
    if  [ -z "$1" ]
    then 
        args=(`realpath .`)
    else
        args=(`realpath ${@:1}`)
    fi
}


function check_args
{
    ### CHECK THE NUMBER OF COMNMAND LINE ARUGMENTS; 1 REQUIRED
    if [ "$1" == "-h" -o  "$1" == "-help" -o  "$1" == "--help" -o ! -d "$1" -o ! -f "$1/SGE_JOB_ID" ] 
    then
        name=`basename $0`
        echo "Usage: 
        $name [DIR1] [DIR2] [DIR3] ...

    DIRs must be valid gpmin experiment directories.
    If no directory is given, then the current directory is considered.  

    "
        exit
    fi
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
    DATE=$(date +"%Y.%m.%d.%H.%M.%S")
    EXP_DIR=$PWD/gpmin'.'$$'.'$GPMIN_GRID_SEED'.'$DATE 
    mkdir -p $EXP_DIR   
    # put together a working directory for spearmint 
    cp $1 $EXP_DIR/config.pb
    cp $SPEARMINT_HOME/generic/job.py $EXP_DIR

    ### SET THE COMMAND TO RUN
    SPEARMINT_GPMIN_CMD=`for str in ${@:2}; do if [ -f "$str" ] ; then realpath $str | tr '\n' ' ' ; else  echo -n ' '$str' ' ;  fi;  done`' $@ '

    echo $SPEARMINT_GPMIN_CMD > $EXP_DIR/job.sh
    echo "" > $EXP_DIR/SGE_JOB_ID

    realpath $EXP_DIR
}


function gpmin_start  
{
    for EXP_DIR in ${args[@]}   
    do
        if [ ! -d "$EXP_DIR" ] 
        then
            echo "Skipping: \"`basename $EXP_DIR`\". Not a valid gpmin directory!"
            continue
        fi

        if [ -f "$EXP_DIR/SGE_JOB_ID" -a -e "$EXP_DIR/SGE_JOB_ID" -a -n "`cat $EXP_DIR/SGE_JOB_ID`" -a -n "$(qstat -s r | grep `cat $EXP_DIR/SGE_JOB_ID` -)" ]
        then
            echo "Skipping: \"`basename $EXP_DIR`\". Job not stopped. Please use the restart option!"
            continue
        fi
        echo "EXPERIMENT: `basename $EXP_DIR`"
            
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

        /dmt3/software/bin/crunch -q $SPEARMINT_QUEUE -o "$EXP_DIR/gpmin.log" -pe omp.pe $SPEARMINT_THREADS  -V -b y "./spearmint.py --method=$SPEARMINT_METHOD --max-concurrent=$GPMIN_MAX_CONCURRENT --max-finished-jobs=$GPMIN_MAX_JOBS --grid-seed=$GPMIN_GRID_SEED $EXP_DIR" > $tfile  

        cat $tfile | tr -cd [0-9.] |  sed -r 's/^([^.]+).*$/\1/; s/^[^0-9]*([0-9]+).*$/\1/' > "$EXP_DIR/SGE_JOB_ID"

        cat $tfile
    done
}


function gpmin_stop
{
    for EXP_DIR in ${args[@]}
    do 
        if [ ! -d "$EXP_DIR" -o ! -f  "$EXP_DIR/SGE_JOB_ID" ]
        then
            echo "Skipping: \"`basename $EXP_DIR`\". Not a valid gpmin experiment!"
            continue
        fi
        if [  -z "`cat $EXP_DIR/SGE_JOB_ID`" ]
        then
            echo "Skipping: \"`basename $EXP_DIR`\". Already stopped!"
            continue
        fi
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
        echo 'STOPPED'
    done
}


