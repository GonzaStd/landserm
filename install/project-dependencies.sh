#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/../.venv"
if [ -d "$VENV_PATH" ]; then
    source "${VENV_PATH}bin/activate"
    if ! "${VENV_PATH}/bin/python" -m pip show pipdeptree > /dev/null 2>&1;then
        "${VENV_PATH}/bin/python" -m pip install pipdeptree
    fi
    pipdeptree --packages "landserm"
else
    echo "You don't have .venv yet!"
fi