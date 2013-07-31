#!/bin/bash
export GPMIN_MAX_CONCURRENT=10
export GPMIN_MAX_JOBS=5000
gpmin $PWD/braninconfig.pb python $PWD/branin.py  

