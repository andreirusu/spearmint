#!/bin/bash

echo $PWD


export PATH=/Users/andreirusu/funspace/cuda/bin:$PATH 
export LD_LIBRARY_PATH=/Users/andreirusu/funspace/cuda/lib64:$LD_LIBRARY_PATH 
export NET_DIR=/Users/andreirusu/funspace/cuda-convnet

# PRINT HYPER-PARAMETERS
echo $epochs_stage1
echo $epochs_stage2
echo $epsW
echo $wc_conv1
echo $wc_conv2
echo $wc_local3
echo $wc_local4
echo $wc_fc10
echo $scale_rnorm
echo $size_rnorm
echo $pow_rnorm

# WRITE CONFIGURATION VALUES
echo $GPU_ID
echo $cost_out_filename


### WRITE CUDA-CONVNET CONFIG FILES
sh $EXP_DIR/layer-params-conv-local-11pct.cfg.sh  
sh $EXP_DIR/layers-conv-local-11pct.cfg.sh


function evaluate {

    rm -Rf $PWD/$1

    SAVE_PATH=$PWD/$1/nets


    mkdir -p $SAVE_PATH
    echo $SAVE_PATH

    RANDOM_SEED=$RANDOM

    ### First train until convergence on batches 1-4 and validate on 5th, for about 350 epochs 
    time python $NET_DIR/convnet.py --seed=$RANDOM_SEED --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH --test-range=5 --train-range=1-4 --layer-def=$PWD/layers.cfg --layer-params=$PWD/params.cfg --data-provider=cifar-cropped --test-freq=$(( 4 * $epochs_stage1 ))  --crop-border=4 --epochs=$epochs_stage1 --gpu=$GPU_ID

    ### Then add 5th batch to training and test on the 6th; continue training for about 150 epochs
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet* --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=$SAVE_PATH --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --test-freq=$(( 5 * $epochs_stage2 )) --epochs=$(( $epochs_stage1 + $epochs_stage2 )) --gpu=$GPU_ID

    ### Then lower learing rate 10 times (uncomment in layer params file); continue training for about 10 epochs
    #time python convnet.py -f ../tmp/tmp/11p3d/ConvNet__2013-07-21_14.02.12 --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=/Users/andreirusu/funspace/tmp/11p --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --layer-params=/Users/andreirusu/funspace/cuda-convnet/example-layers/layer-params-conv-local-11pct-3d.cfg --test-freq=10 --epochs 510 --gpu 0

    ### Then lower learing rate 10 times once again (uncomment in layer params file); continue training for about 10 epochs
    #time python convnet.py -f ../tmp/tmp/tmp/11p3d/ConvNet__2013-07-21_14.02.12 --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --save-path=/Users/andreirusu/funspace/tmp/11p --test-range=6 --train-range=1-5 --data-provider=cifar-cropped --test-freq=5 --layer-params=/Users/andreirusu/funspace/cuda-convnet/example-layers/layer-params-conv-local-11pct-3d.cfg --epochs 520 --gpu 0

    ### TEST => 0.1111 error; accuracy > 88% 
    time python $NET_DIR/convnet.py -f $SAVE_PATH/ConvNet* --logreg-name=logprob --data-path=/Users/andreirusu/funspace/cifar-10-py-colmajor --test-only=1 --multiview-test=1 --test-range=6 --data-provider=cifar-cropped --gpu $GPU_ID > $SAVE_PATH/test.txt
    cat $SAVE_PATH/test.txt
}


function cost {
    cat $PWD/$1/nets/test.txt  | grep logprob - | tail -n1 | cut -d ' ' -f 4 
}


### RUN EXPERIMENTS
count=5
for i in `seq 0 $(($count - 1))` 
do
    evaluate $i
done  


## AVERAGE OVER EXPERIMENTS
avg=0
for i in `seq 0 $(($count - 1))` 
do
    c=`cost $i`
    echo $c
    avg=` echo "$c + $avg" | bc -l `
done    
avg=`echo "$avg / $count" | bc -l`


#### WRITE RESUL
echo $avg > $cost_out_filename

