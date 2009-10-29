#!/bin/bash

cd $1/..
if [ -d inyoka-testsite/bin/activate ]; then
	source inyoka-testsuite/bin/activate
fi
cd $1
make runtests
