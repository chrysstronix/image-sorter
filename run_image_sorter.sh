#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_PYTHON="$SCRIPT_DIR/venv_imagesorter/bin/python"

if [ -x "$VENV_PYTHON" ]; then
    exec "$VENV_PYTHON" "$SCRIPT_DIR/run_image_sorter.py" "$@"
fi

VENV_PYTHON="$SCRIPT_DIR/../venv_imagesorter/bin/python"
if [ -x "$VENV_PYTHON" ]; then
    exec "$VENV_PYTHON" "$SCRIPT_DIR/run_image_sorter.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/run_image_sorter.py" "$@"
fi

printf '%s\n' "Python 3 was not found. Install Python 3.10 or later to run Image Sorter." >&2
exit 1
