#!/bin/bash

cd /home/vagrant/python/venv
source bbs/bin/activate
cd ../code/bbs
cd test_tools
/usr/bin/python3 dat_fall.py >> python.log
