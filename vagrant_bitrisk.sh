#!/bin/sh

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd SCRIPT_DIR

export VENV_PATH=$HOME
python setup_dependancies.py
export HOST=0.0.0.0
python run.py debug
