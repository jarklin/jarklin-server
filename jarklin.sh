#!/usr/bin/env bash
set -e

THIS=$(dirname "$(realpath "$0")")

PYTHON3="$THIS/.venv/bin/python3"

if [ ! -f "$PYTHON3" ]; then
  PYTHON3=$(/usr/bin/env python3)
fi

PYTHONPATH="$PYTHONPATH:$THIS/src/" "$PYTHON3" -X utf8 -BO -m jarklin "$@"
