#!/bin/sh
set -eu
python -m compileall -q app
python run_tests.py
