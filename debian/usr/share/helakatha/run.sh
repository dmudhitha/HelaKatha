#!/bin/bash
# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Force X11 backend for PyQt (necessary on Wayland systems via Xwayland)
export QT_QPA_PLATFORM=xcb

# Execute main.py using the virtual environment python
"$DIR/.venv/bin/python3" "$DIR/main.py"
