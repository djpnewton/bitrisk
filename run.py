#!/usr/bin/python

import subprocess
import sys
import os

# setup constants
venv_path = '.'
if os.environ.has_key('VENV_PATH'):
    venv_path = os.environ['VENV_PATH']
VENV = '%s/venv' % venv_path
PYTHON = '%s/bin/python' % VENV
if os.name == 'nt':
    PYTHON = r'%s\scripts\python' % VENV

# command helper
def call(args):
    rc = subprocess.call(args)
    if rc:
        sys.exit(rc)

# change to directory of this script
basedir = os.path.dirname(os.path.realpath(__file__))
os.chdir(basedir)

# run server using virtual environment
args = [PYTHON] + sys.argv[1:] 
call(args)
