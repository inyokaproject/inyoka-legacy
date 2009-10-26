#!/bin/bash

python $1/make-bootstrap.py > $1/../bootstrap.py
cd $1/..
python bootstrap.py inyoka-testsuite
source inyoka-testsuite/bin/activate 
cd $1
make runtests
