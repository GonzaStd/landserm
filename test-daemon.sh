#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source .venv/bin/activate
export PYTHONPATH="$(pwd)"
python3 landserm/daemon/daemon.py
