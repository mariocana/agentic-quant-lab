#!/bin/bash
# Avvia tutti i frontend del repo e li apre nel browser.
#
#   1. quantlake dashboard   http://127.0.0.1:8000    FastAPI + React dal laboratorio (vedi $QL), schede DATI / COT / EQUITY:
#                                                     l'Equity desk sono montati dentro (/cot, /equity). Il frontend
#                                                     si ricompila da solo se i sorgenti sono cambiati (serve npm)
#   2. AI desk               http://127.0.0.1:8765    repo a parte (vedi $AI_DESK_DIR), saltato se non c'è
#
# Uso:
#   ./start_frontends.sh              avvia tutto e apre il browser
#   ./start_frontends.sh --no-open    senza aprire il browser
#   ./start_frontends.sh --rebuild    ricompila il frontend React della dashboard
#
# Ctrl+C ferma tutto. Log in <laboratorio>/quantlake/data/logs/frontends/.
# Variabili: QL (default ../agentic-quant-lab/quantlake: il laboratorio e un repo
#            a parte), PY (python di quantlake, default $QL/.venv/bin/python),
#            AI_DESK_DIR (default $QL/../ai-desk), DASHBOARD_PORT, AI_DESK_PORT.
# COT ed Equity desk girano anche da soli (python applications/cot_desk/app.py, .../equity_desk/app.py).

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
QL="${QL:-$(cd "$ROOT/.." && pwd)/agentic-quant-lab/quantlake}"   # repo a parte da ottobre 2026
PY="${PY:-$QL/.venv/bin/python}"
AI_DESK_DIR="${AI_DESK_DIR:-$QL/../ai-desk}"   # pacchetto del laboratorio da ottobre 2026
DASHBOARD_PORT="${DASHBOARD_PORT:-8000}"
AI_DESK_PORT="${AI_DESK_PORT:-8765}"
LOGS="$QL/data/logs/frontends"

OPEN=1
DASH_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --no-open) OPEN=0 ;;
    --rebuild) DASH_ARGS+=(--rebuild) ;;
    -h|--help) sed -n 2,18p "$0"; exit 0 ;;
    *) echo "argomento sconosciuto: $arg (usa --help)"; exit 2 ;;
  esac
done

open_url() {
  [ "$OPEN" = 1 ] || return 0
  if command -v open >/dev/null; then open "$1"            # macOS
  elif command -v xdg-open >/dev/null; then xdg-open "$1" >/dev/null 2>&1
  fi
}

port_busy() { curl -s --noproxy '*' -o /dev/null -m 1 "http://127.0.0.1:$1/"; }

wait_up() {  # wait_up <name> <url> <pid>
  for _ in $(seq 1 240); do
    if curl -s --noproxy '*' -o /dev/null -m 1 -f "$2"; then return 0; fi
    if ! kill -0 "$3" 2>/dev/null; then
      echo "   ✗ si è fermato, ultime righe di $LOGS/$1.log:"; tail -5 "$LOGS/$1.log" | sed 's/^/     /'
      return 1
    fi
    sleep 0.5
  done
  echo "   ✗ non risponde dopo 2 minuti, vedi $LOGS/$1.log"; return 1
}

PIDS=()
cleanup() {
  echo; echo "Fermo i frontend..."
  for pid in ${PIDS[@]+"${PIDS[@]}"}; do kill "$pid" 2>/dev/null; done
  wait 2>/dev/null
  exit 0
}
trap cleanup INT TERM

start() {  # start <name> <port> <health-url> <cmd...>
  local name=$1 port=$2 health=$3; shift 3
  if port_busy "$port"; then
    echo "   · porta $port già in uso, lo considero già avviato"
    open_url "http://127.0.0.1:$port"
    return
  fi
  "$@" > "$LOGS/$name.log" 2>&1 &
  local pid=$!
  PIDS+=("$pid")
  if wait_up "$name" "$health" "$pid"; then
    echo "   ✓ http://127.0.0.1:$port"
    open_url "http://127.0.0.1:$port"
  fi
}

mkdir -p "$LOGS"


if [ -x "$PY" ]; then
  export PYTHONPATH="$QL/src${PYTHONPATH:+:$PYTHONPATH}"
  echo "1. quantlake dashboard + COT + Equity (compila il frontend React se è cambiato, ~1 min)"
  start dashboard "$DASHBOARD_PORT" "http://127.0.0.1:$DASHBOARD_PORT/api/layers" \
    bash -c 'cd "$1" && shift && exec "$@"' _ "$QL" \
    "$PY" -m quantlake.dashboard.cli --no-browser --port "$DASHBOARD_PORT" ${DASH_ARGS[@]+"${DASH_ARGS[@]}"}
else
  echo "1. quantlake: python non trovato in $PY, esegui 'poetry install' in python/quantlake"
fi

echo "2. AI desk"
if [ ! -d "$AI_DESK_DIR" ]; then
  echo "   · $AI_DESK_DIR non c'è (è sul branch features/ai-desk), salto"
elif [ ! -x "$AI_DESK_DIR/.venv/bin/desk" ]; then
  echo "   ✗ venv mancante: cd python/ai-desk && uv venv --python 3.12 && uv pip install -e ."
else
  # cwd = python/ai-desk: config/ e var/ sono relativi alla cartella del progetto
  start ai_desk "$AI_DESK_PORT" "http://127.0.0.1:$AI_DESK_PORT/" \
    bash -c 'cd "$1" && exec .venv/bin/desk ui --port "$2"' _ "$AI_DESK_DIR" "$AI_DESK_PORT"
fi

if [ ${#PIDS[@]} -eq 0 ]; then
  echo; echo "Nessun server avviato da questo script."
  exit 0
fi
echo
echo "Tutto avviato. Ctrl+C per fermare."
wait
