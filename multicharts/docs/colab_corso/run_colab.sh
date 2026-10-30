#!/bin/sh
# Python di quantlake (pandas, matplotlib) + openpyxl in ./libs + finto google.colab.
# Prima volta: uv pip install --target mc/docs/colab_corso/libs --python python/quantlake/.venv/bin/python openpyxl
D=$(cd "$(dirname "$0")" && pwd)
MPLBACKEND=Agg PYTHONPATH="$D:$D/libs" exec "$D/../../../python/quantlake/.venv/bin/python" -W ignore "$D/run_colab.py" "$@"
