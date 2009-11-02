#!/bin/bash

cd $1/..
if [ -f inyoka-testsuite/bin/activate ]; then
	source inyoka-testsuite/bin/activate
fi
cd $1
find inyoka -name "*.pyc" -delete
make runtests
