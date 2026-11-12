#!/bin/bash
# Avvia la pagina unica del laboratorio e la apre nel browser: http://127.0.0.1:8000
#
#   Dati, COT, Equity   quantlake (le sue tabelle e i suoi desk)
#   Hyperliquid bridge  il connettore su Railway, attraverso il server (password presa da quantlake/.env)
#   Laboratorio         registro delle prove e idee in fabbrica
#
# Uso:
#   ./start_frontends.sh              compila la shell se i sorgenti sono cambiati, avvia, apre il browser
#   ./start_frontends.sh --no-open    senza aprire il browser
#   ./start_frontends.sh --rebuild    ricompila comunque la shell React (fe/web)
#
# Il server ascolta solo su 127.0.0.1: da qui si comanda il desk (kill switch, flatten),
# quindi non va mai esposto. Ctrl+C lo ferma. Variabile: PORT (default 8000).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8000}"
OPEN=1; REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --no-open) OPEN=0 ;;
    --rebuild) REBUILD=1 ;;
    -h|--help) sed -n 2,14p "$0"; exit 0 ;;
    *) echo "argomento sconosciuto: $arg (usa --help)"; exit 2 ;;
  esac
done

WEB="$ROOT/fe/web"
DIST="$WEB/dist/index.html"
stale() { [ ! -f "$DIST" ] || [ -n "$(find "$WEB/src" "$WEB/index.html" -newer "$DIST" -print -quit)" ]; }
if [ "$REBUILD" = 1 ] || stale; then
  echo "· compilo la shell (fe/web)…"
  ( cd "$WEB" && { [ -d node_modules ] || npm install --no-audit --no-fund --loglevel=error; } && npm run build >/dev/null )
fi

if [ "$OPEN" = 1 ]; then
  ( for _ in $(seq 1 60); do
      curl -fs "http://127.0.0.1:$PORT/api/apps" >/dev/null 2>&1 && { open "http://127.0.0.1:$PORT"; exit; }
      sleep 1
    done ) &
fi
echo "· http://127.0.0.1:$PORT  (Ctrl+C per fermare)"
cd "$ROOT/quantlake" && exec poetry run python ../fe/server.py "$PORT"
