#!/bin/bash

function dec {
    printf "%.10f" $1
}

function div {
    e=`printf "%.10f / %.10f" $1 $2`
    res=`echo $e | bc -l`
    dec $res
}


function layer_conf { 
echo "[conv1]
epsW=`div $epsW $1`
epsB=0.002
momW=0.9
momB=0.9
wc=`dec $wc_conv1`

[conv2]
epsW=`div $epsW $1`
epsB=0.002
momW=0.9
momB=0.9
wc=`dec $wc_conv2`

[local3]
epsW=`div $epsW $1`
epsB=0.002
momW=0.9
momB=0.9
wc=`dec $wc_local3`

[local4]
epsW=`div $epsW $1`
epsB=0.002
momW=0.9
momB=0.9
wc=`dec $wc_local4`

[fc10]
epsW=`div $epsW $1`
epsB=0.002
momW=0.9
momB=0.9
wc=`dec $wc_fc10`

[logprob]
coeff=1

[rnorm1]
scale=`dec $scale_rnorm`
pow=`dec $pow_rnorm`

[rnorm2]
scale=`dec $scale_rnorm`
pow=`dec $pow_rnorm`
     "
}

layer_conf 1 | tr " " "\n" > "params.cfg"
layer_conf 10 | tr " " "\n" > "params_lower_epsW_10.cfg"
layer_conf 100 | tr " " "\n" > "params_lower_epsW_100.cfg"

