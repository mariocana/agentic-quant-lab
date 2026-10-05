# COT Positioning Desk

Local web UI for the weekly CFTC Commitments of Traders, migrated from the
`cot-analyzer` project (Railway + Postgres). It now reads
`gold/cot_positioning/1w` from quantlake.

## Pipeline

```
CFTC API ──▶ historical/cftc_cot.py ──▶ bronze/cftc_cot
                                         │
             historical/cot_positioning.py
                                         ▼
                        silver/cftc_cot ──▶ gold/cot_positioning/1w ──▶ cot_desk
```

- No scheduled job: press **SYNC** in the UI. It checks whether a new
  report should exist (published Friday 15:30 ET) and, only if gold is
  stale, runs the two scripts above. The first press downloads the full
  history since 1986 (about a minute).

## Run

From `python/quantlake`:

```bash
.venv/bin/python applications/cot_desk/app.py                # http://127.0.0.1:5050, then SYNC
```

The scripts also run by hand, without the UI:

```bash
.venv/bin/python applications/historical/cftc_cot.py [EUR GC …]
.venv/bin/python applications/historical/cot_positioning.py
```

## `.env`

| Key | Use |
|---|---|
| `ANTHROPIC_API_KEY` | AI review (top-3 and single asset). Without it the buttons say the key is missing. |
| `COT_AI_MODEL` | Optional, default `claude-opus-5-5`. |
| `CFTC_APP_TOKEN` | Optional Socrata token, avoids 403 / rate limits. |
| `COT_DESK_PORT` | Optional, default `5050`. |

## Files

- `app.py` — Flask routes (same JSON contract as cot-analyzer, so the templates are unchanged)
- `core.py` — pair biases, classification, top-3, AI prompts (logic unchanged)
- `store.py` — reads the gold Delta table (replaces `db.py`)
- `sync.py` — freshness check + runs the quantlake scripts (replaces the CFTC client)
- `instruments.py` — ticker lookup over `applications/symbols.py` `COT_INSTRUMENTS`
