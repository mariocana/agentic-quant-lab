#!/bin/bash
# Raccolta dati automatica (chiamata da launchd).
#   raccolta.sh chain   -> foto della catena SPX
#   raccolta.sh daily   -> VIX/VIX9D/VIX1D/VIX3M/VXN + GEX SqueezeMetrics + NDX, poi contesto giornaliero
#   raccolta.sh gold    -> MultiCharts bronze/silver + gold OHLCV letti da alpha-quant + contesto giornaliero
#   raccolta.sh earnings -> calendario trimestrali, sorprese EPS, prezzi azioni + earnings screener
#   raccolta.sh maintain -> compatta + vacuum delle tabelle Delta (a runner live fermi)
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
echo "=== $(date '+%F %T') $1"
case "$1" in
  chain) $PY applications/spx_chain_snapshot.py ;;
  daily) $PY applications/historical/cboe_vix.py && $PY applications/historical/squeezemetrics.py \
         && $PY applications/historical/nasdaq_index.py && $PY applications/historical/daily_context.py ;;
  gold) $PY applications/historical/multicharts.py && $PY applications/historical/ohlcv_gold.py \
        && $PY applications/historical/daily_context.py && $PY applications/historical/multicharts_rolls.py ;;
  earnings) $PY applications/historical/earnings.py ;;
  maintain) $PY -m quantlake.maintenance ;;
  *) echo "uso: $0 chain|daily|gold|earnings|maintain"; exit 1 ;;
esac
