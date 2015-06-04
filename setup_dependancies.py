#!/usr/bin/env python

import subprocess
import sys
import os

# setup constants
venv_path = '.'
if os.environ.has_key('VENV_PATH'):
    venv_path = os.environ['VENV_PATH']
VENV = '%s/venv' % venv_path
VIRTUALENV = 'virtualenv'
PIP = '%s/bin/pip' % VENV
BOWER = 'bower'
if os.name == 'nt':
    VIRTUALENV = r'c:\python27\scripts\virtualenv.exe'
    PIP = r'%s\scripts\pip' % VENV
    BOWER = 'bower'

# command helper
def call(args, shell=False):
    rc = subprocess.call(args, shell=shell)
    if rc:
        sys.exit(rc)

# change to directory of this script
basedir = os.path.dirname(os.path.realpath(__file__))
os.chdir(basedir)

# install virtual environment
if not os.path.isdir(VENV):
    call([VIRTUALENV, VENV])
call([PIP, 'install', '-r', 'requirements.txt'])

# install bower dependencies
shell=False
if os.name == 'nt':
    shell=True
call([BOWER, '--allow-root', '--config.interactive=false', 'install'], shell)
