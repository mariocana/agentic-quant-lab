#!/bin/bash
# One desk cycle, for launchd. Paper mode writes the same var/ files the UI reads.
#
# launchd gives a job almost no environment, so everything here is absolute.
# Exit non-zero only when the cycle itself fails: launchd logs it and moves on.
set -uo pipefail

DESK="/Users/mario/Documents/Repo/my-codes/python/ai-desk"
cd "$DESK" || exit 1
mkdir -p var

echo "=== $(date -u '+%Y-%m-%dT%H:%M:%SZ') cycle start ==="

# Refuse to run while the UI's own scheduler could fire: two processes writing the
# same paper account would race, and the lock only covers one process.
if [ -f var/ui_settings.json ] && /usr/bin/grep -q '"schedule_enabled": true' var/ui_settings.json; then
  echo "SKIPPED: the UI scheduler is enabled. Turn it off in the dashboard (Desk > Schedule)"
  echo "         or disable this launchd job — only one of the two may run cycles."
  exit 0
fi

"$DESK/.venv/bin/desk" run
STATUS=$?
echo "=== $(date -u '+%Y-%m-%dT%H:%M:%SZ') cycle end (exit $STATUS) ==="
exit $STATUS
