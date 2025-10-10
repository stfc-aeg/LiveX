#!/bin/bash

# config
VENV_NAME="venv-livex"
APP_BUILD_URL="https://github.com/stfc-aeg/LiveX/releases/download/v0.2.5/app_build.tgz"

# get root of repo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "---"
echo "LiveX installation starting from $REPO_ROOT"

# Ensure script is starting from the right place
if [ ! -d "$REPO_ROOT/control" ]; then
    echo "Error: this script must be run from inside the livex repository (i.e. livex/docs/install.sh)"
    exit 1
fi

cd "$REPO_ROOT/.."
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating venv"
    python -m venv "$VENV_NAME"
else
    echo "Venv already exists, skipping"
fi

source "$VENV_NAME/bin/activate"
echo "---"
echo "Virtual environment activated"

# Onto installation
cd "$REPO_ROOT"
git submodule update --init
echo "---"
echo "Submodules initialized"

pip install -e control/.
pip install odin-sequencer/.
pip install munir/.
pip install odin-orca-quest/control/.
pip install odin-kinesis/.
echo "---"
echo "Installed modules"

# UI
STATIC_DIR="$REPO_ROOT/control/test/static"
cd "$STATIC_DIR"

echo "---"
echo "Getting UI build"
curl -L -o app_build.tgz "$APP_BUILD_URL"
echo "Extracting UI build"
tar -xzvf app_build.tgz

if [ -d "dist" ]; then
    mv sequencer.html dist/
    mv js dist/
    mv css dist/
else
    echo "Error: dist not found after extraction"
    exit 1
fi

echo "---"
echo "UI assets placed in static path"

echo "---"
echo "Installation complete. Please see this script for instructions on use."

# Before using the software, you must:
# - activate the virtual environment `source <venv>/bin/activate`
# - edit the config as needed in `control/test/config/livex.cfg`
# - run from control/ with `odin_control --config test/config/livex.cfg`
# - open browser to address specified in config

