#!/bin/sh
# Python di quantlake (pandas, matplotlib) + openpyxl in ./libs + finto google.colab.
# Prima volta: uv venv --python 3.13 docs/colab_corso/.venv && uv pip install --python docs/colab_corso/.venv/bin/python numpy pandas matplotlib openpyxl
D=$(cd "$(dirname "$0")" && pwd)
MPLBACKEND=Agg PYTHONPATH="$D" exec "$D/.venv/bin/python" -W ignore "$D/run_colab.py" "$@"
