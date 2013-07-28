#!/bin/bash

layer_conf="[conv1]
epsW=$epsW
epsB=0.002
momW=0.9
momB=0.9
wc=$wc_conv1

[conv2]
epsW=$epsW
epsB=0.002
momW=0.9
momB=0.9
wc=$wc_conv2

[local3]
epsW=$epsW
epsB=0.002
momW=0.9
momB=0.9
wc=$wc_local3

[local4]
epsW=$epsW
epsB=0.002
momW=0.9
momB=0.9
wc=$wc_local4

[fc10]
epsW=$epsW
epsB=0.002
momW=0.9
momB=0.9
wc=$wc_fc10

[logprob]
coeff=1

[rnorm1]
scale=$scale_rnorm
pow=$pow_rnorm

[rnorm2]
scale=$scale_rnorm
pow=$pow_rnorm
 "

echo $layer_conf | tr " " "\n" > "params.cfg"

