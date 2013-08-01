#!/bin/bash 

function dec {
    printf "%.10f\n" $1
}

function div {
    if [ -z "$1" -o -z "$2" ] 
    then
        echo "ERROR in div $1 $2 " 1>&2
        exit
    fi
    e=`printf "%.16f / %.16f" $1 $2`
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

echo "`layer_conf 1`"       > "params.cfg"
echo "`layer_conf 10`"      > "params_lower_epsW_10.cfg"
echo "`layer_conf 100`"     > "params_lower_epsW_100.cfg"

