#!/bin/bash
export GPMIN_MAX_CONCURRENT=100
export GPMIN_MAX_JOBS=5000
gpmin braninconfig.pb  python $PWD/branin.py  

