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

- Weekly job: `applications/raccolta.sh weekly` (launchd
  `com.mario.quantlake.weekly`, Saturday 09:00).
- The **SYNC** button in the UI runs the same two scripts on demand.

## Run

From `python/quantlake`:

```bash
.venv/bin/python applications/historical/cftc_cot.py         # first run: full history since 1986
.venv/bin/python applications/historical/cot_positioning.py
.venv/bin/python applications/cot_desk/app.py                # http://127.0.0.1:5050
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
