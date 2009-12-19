#!/bin/bash

cd ../..
if [ -f inyoka-testsuite/bin/activate ]; then
	source inyoka-testsuite/bin/activate
fi
cd ..
find inyoka -name "*.pyc" -delete
fab runtests
