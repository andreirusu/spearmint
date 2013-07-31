#!/bin/bash

echo "[data]
type=data
dataIdx=0
 
[labels]
type=data
dataIdx=1
 
[conv1]
type=conv
inputs=data
channels=3
filters=64
padding=2
stride=1
filterSize=5
neuron=relu
initW=0.0001
partialSum=4
sharedBiases=1
 
[pool1]
type=pool
pool=max
inputs=conv1
start=0
sizeX=3
stride=2
outputsX=0
channels=64
 
[rnorm1]
type=cmrnorm
inputs=pool1
channels=64
size=$size_rnorm
 
[conv2]
type=conv
inputs=rnorm1
filters=64
padding=2
stride=1
filterSize=5
channels=64
neuron=relu
initW=0.01
partialSum=8
sharedBiases=1
 
[rnorm2]
type=cmrnorm
inputs=conv2
channels=64
size=$size_rnorm
 
[pool2]
type=pool
pool=max
inputs=rnorm2
start=0
sizeX=3
stride=2
outputsX=0
channels=64
 
[local3]
type=local
inputs=pool2
filters=64
padding=1
stride=1
filterSize=3
channels=64
neuron=relu
initW=0.04
 
[local4]
type=local
inputs=local3
filters=32
padding=1
stride=1
filterSize=3
channels=64
neuron=relu
initW=0.04
 
[fc10]
type=fc
outputs=10
inputs=local4
initW=0.01
 
[probs]
type=softmax
inputs=fc10
 
[logprob]
type=cost.logreg
inputs=labels,probs
 
"  > "layers.cfg"

