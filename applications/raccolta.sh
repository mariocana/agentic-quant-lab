#!/bin/bash
# Raccolta dati automatica (chiamata da launchd).
#   raccolta.sh chain   -> foto della catena SPX
#   raccolta.sh daily   -> VIX/VIX9D/VIX1D/VIX3M + GEX SqueezeMetrics
#   raccolta.sh weekly  -> CFTC Commitments of Traders
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
echo "=== $(date '+%F %T') $1"
case "$1" in
  chain) $PY applications/spx_chain_snapshot.py ;;
  daily) $PY applications/historical/cboe_vix.py && $PY applications/historical/squeezemetrics.py ;;
  weekly) $PY applications/historical/cftc_cot.py; $PY applications/historical/cot_positioning.py ;;
  *) echo "uso: $0 chain|daily|weekly"; exit 1 ;;
esac
