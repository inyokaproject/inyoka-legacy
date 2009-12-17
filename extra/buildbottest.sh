#!/bin/bash

cd $1/..
if [ -f inyoka-testsuite/bin/activate ]; then
	source inyoka-testsuite/bin/activate
fi
cd $1
find inyoka -name "*.pyc" -delete
if [ -f .coverage ]; then
	rm .coverage
fi
if [ -f .noseids ]; then
	rm .noseids
fi
fab runtests
