#!/bin/bash -e   

echo 'CHECKING REQUIRED VARIABLES ARE SET'
echo ${EXP_DIR:?} 
echo ${epochs_stage1:?} 
echo ${epochs_stage2:?} 
echo ${epsW:?}
echo ${wc_conv1:?}
echo ${wc_conv2:?}
echo ${wc_local3:?}
echo ${wc_local4:?}
echo ${wc_fc10:?}
echo ${scale_rnorm:?}
echo ${size_rnorm:?}
echo ${pow_rnorm:?} 


export PATH=/Users/andreirusu/funspace/cuda/bin:$PATH 
export LD_LIBRARY_PATH=/Users/andreirusu/funspace/cuda/lib64:$LD_LIBRARY_PATH 
export NET_DIR=/Users/andreirusu/funspace/cuda-convnet

function real_dir_path 
{
    echo "$(dirname $(readlink -e $1))/$(basename $1)" 
}

echo "PWD: $PWD"
echo "EXP_DIR: $EXP_DIR"

echo 'PRINT HYPER-PARAMETERS'

printf  "epochs_stage1: %f\nepochs_stage2: %f\nepsW: %f\nwc_conv1: %f\nwc_conv2: %f\nwc_local3: %f\nwc_local4: %f\nwc_fc10: %f\nscale_rnorm: %f\nsize_rnorm: %f\npow_rnorm: %f\n" $epochs_stage1 $epochs_stage2 $epsW $wc_conv1 $wc_conv2 $wc_local3 $wc_local4 $wc_fc10 $scale_rnorm $size_rnorm $pow_rnorm

echo 'WRITE CONFIGURATION VALUES'
echo "GPU_ID: $GPU_ID"
echo "OUTFILE: $cost_out_filename"


echo 'WRITE CUDA-CONVNET CONFIG FILES'
/bin/bash $EXP_DIR/layer-params-conv-local-11pct.cfg.sh  
/bin/bash $EXP_DIR/layers-conv-local-11pct.cfg.sh

function evaluate {

    rm -Rf $PWD/$1

    SAVE_PATH=$PWD/$1

    mkdir -p $SAVE_PATH
    echo $SAVE_PATH

    RANDOM_SEED=$RANDOM

    echo 'First train until convergence on batches 1-4 and validate on 5th, for about some epochs' 
    time python $NET_DIR/convnet.py --seed=$RANDOM_SEED --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH --test-range=5 --train-range=1-4 --layer-def=$PWD/layers.cfg --layer-params=$PWD/params.cfg --data-provider=cifar-cropped --test-freq=$epochs_stage1  --crop-border=4 --epochs=$epochs_stage1 --gpu=$GPU_ID

    echo 'Then add 5th batch to training and test on the 6th; continue training for about 150 epochs'
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet*   --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH  --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --test-freq=$epochs_stage2 --epochs=$(( $epochs_stage1 + $epochs_stage2 )) --gpu=$GPU_ID

    echo 'Then lower learing rate 10 times (uncomment in layer params file); continue training for about 10 epochs'
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet*   --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH  --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --test-freq=50 --layer-params=$PWD/params_lower_epsW_10.cfg --epochs=$(( $epochs_stage1 + $epochs_stage2 + 50 )) --gpu=$GPU_ID

    echo 'Then lower learing rate 10 times once again (uncomment in layer params file); continue training for about 10 epochs'
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet*   --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH  --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --test-freq=50 --layer-params=$PWD/params_lower_epsW_100.cfg  --epochs=$(( $epochs_stage1 + $epochs_stage2 + 100)) --gpu=$GPU_ID

    echo 'MULTIVIEW TEST'
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet* --logreg-name=logprob --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --test-only=1 --multiview-test=1 --test-range=6 --data-provider=cifar-cropped --gpu $GPU_ID > $SAVE_PATH/test.txt
    echo "SAVE TEST OUTPUT TO $SAVE_PATH/test.txt"
    cat $SAVE_PATH/test.txt
}


function cost {
    echo "EXTRACTING COST"
    cat $PWD/$1/test.txt  | grep logprob - | tail -n1 | cut -d ' ' -f 4 
}


echo 'RUN EXPERIMENTS'
count=5
for i in `seq 0 $(($count - 1))` 
do
    echo "STARTING EXPERIMENT $i"
    evaluate $i
done  


echo 'AVERAGE OVER EXPERIMENTS'
avg=0
for i in `seq 0 $(($count - 1))` 
do
    c=`cost $i`
    echo "EXPERIMENT $i : $c"
    avg=` echo "$c + $avg" | bc -l `
done    
avg=`echo "$avg / $count" | bc -l`


echo "AVERAGE COST: $avg"

echo 'WRITE RESULT'
if [ -n "$avg" ]
then
    printf "%.7f\n" $avg > $cost_out_filename
fi

