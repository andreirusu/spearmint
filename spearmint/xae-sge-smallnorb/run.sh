#!/bin/bash
echo "Current directory: "`pwd`
echo "Current experiment: "`dirname $0`
python spearmint.py --method=GPEIOptChooser --max-concurrent=10 --max-finished-jobs=200 --grid-seed=1 `dirname $0`
