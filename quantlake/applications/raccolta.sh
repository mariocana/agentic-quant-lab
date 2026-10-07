#!/bin/bash
# Raccolta dati automatica (chiamata da launchd).
#   raccolta.sh chain   -> foto della catena SPX
#   raccolta.sh daily   -> VIX/VIX9D/VIX1D/VIX3M + GEX SqueezeMetrics
#   raccolta.sh maintain -> compatta + vacuum delle tabelle Delta (a runner live fermi)
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
echo "=== $(date '+%F %T') $1"
case "$1" in
  chain) $PY applications/spx_chain_snapshot.py ;;
  daily) $PY applications/historical/cboe_vix.py && $PY applications/historical/squeezemetrics.py ;;
  maintain) $PY -m quantlake.maintenance ;;
  *) echo "uso: $0 chain|daily|maintain"; exit 1 ;;
esac
