#!/bin/bash

cd $1/..
source inyoka-testsuite/bin/activate 
cd $1
make runtests
