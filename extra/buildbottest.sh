#!/bin/bash

if [ -f ../inyoka-testsuite/bin/activate ]; then
	source ../inyoka-testsuite/bin/activate
fi
find inyoka -name "*.pyc" -delete
fab test
