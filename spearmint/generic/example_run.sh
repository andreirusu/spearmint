#!/bin/bash
export GPMIN_MAX_CONCURRENT=500
export GPMIN_MAX_JOBS=2000
gpmin braninconfig.pb  python $PWD/branin.py  

