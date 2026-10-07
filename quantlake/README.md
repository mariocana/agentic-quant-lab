# quantlake

Local trading database built on Delta Lake, with a bronze → silver → gold
medallion layout. It ingests market, macro, on-chain, agricultural and
positioning data, cleans it, and builds resampled bars with features
(via [Oryon](https://pypi.org/project/oryon/)) for research and live
strategies.

```
source APIs ──▶ bronze  raw rows, one table per source
                  │      clean_ohlcv: invalid values → NaN, rows never dropped
                  ▼
                silver  cleaned, plus composite tables (e.g. macro_ohlcv)
                  │      resample + transform_gold + features
                  ▼
                gold    <strategy>/<timeframe>, ready for backtests and live signals
```

Next to the three layers, `reference/` holds tables that are not time
series. `reference/instruments` has one row per instrument with its market
specs (tick size, multiplier, quantity step, exchange calendar) and the
gold table holding its bars. alpha-quant reads it read-only, so its schema
is a contract (`src/quantlake/reference/instruments.py`).

`workflow.yaml` is the full map of sources, tables and the transforms
between them; the dashboard draws it as a graph.

## Install

Python 3.13 and Poetry:

```bash
cd python/quantlake
poetry install                                       # everything
poetry install --without geo,research,desk,dashboard # core pipeline only
```

| Group       | For                                                         |
|-------------|-------------------------------------------------------------|
| (core)      | bronze/silver/gold, connectors, live runners                |
| `dashboard` | `poetry run dashboard` (FastAPI + DuckDB)                   |
| `geo`       | Sentinel-2 / USDA CDL connectors, `examples/satelite_exercise` |
| `research`  | notebooks, `applications/live/ml_based_strategy` (scikit-learn model) |
| `desk`      | `applications/cot_desk` (Flask + Anthropic)                 |
| `dev`       | pytest, Jupyter                                             |

## Configuration

Credentials are read from a `.env` in `python/quantlake`. Only the keys of
the sources you use are needed.

| Variable | Used by |
|----------|---------|
| `QUANTLAKE_DATA_ROOT` | where tables live (default `python/quantlake/data`) |
| `CAPITAL_API_KEY`, `CAPITAL_LOGIN`, `CAPITAL_PASSWORD` | Capital.com |
| `FRED_API_KEY` | FRED |
| `DUNE_API_KEY` | Dune |
| `OWL_API_KEY` | Owlracle |
| `NASS_API_KEY` | USDA NASS |
| `CFTC_APP_TOKEN` | CFTC COT (optional, raises the rate limit) |
| `ANTHROPIC_API_KEY`, `COT_AI_MODEL`, `COT_DESK_PORT` | COT desk |

## Layout

```
src/quantlake/
  bronze/connectors/   one connector per source (HistoricalConnector / StreamConnector)
  bronze/ silver/ gold/  ingest + save per layer, all through storage.upsert
  storage.py           idempotent Delta upsert, partitioned by (symbol, year, month)
  live.py              WebSocket runner: gap fill, crash recovery, in-memory hot path
  maintenance.py       compact + vacuum
  reference/           instruments table (market specs, read by alpha-quant)
  dashboard/           FastAPI backend of the dashboard
applications/
  historical/          bootstrap / resumable backfills, one script per source
  live/                live strategies (poll-based or WebSocket via live.run)
  cot_desk/            COT positioning UI (see its README)
dashboard/             React frontend
examples/              small per-layer examples and notebooks
launchd/               macOS scheduled jobs
```

Every write merges on `(symbol, timestamp)`, so re-running an ingest over
the same range never creates duplicates.

## Run

```bash
poetry run python applications/historical/binance.py   # backfill a source
poetry run python applications/live/macro.py           # a live strategy
poetry run dashboard                                   # http://127.0.0.1:8000
poetry run maintain                                    # compact + vacuum all tables
poetry run python examples/reference/seed_instruments.py  # create/update reference/instruments
```

`../../start_frontends.sh` starts the dashboard and the COT desk together.

### Scheduled jobs (macOS)

`applications/raccolta.sh` is the entry point for launchd:

| Job | When | What |
|-----|------|------|
| `com.mario.quantlake.daily` | weekdays 07:30 | VIX indices + SqueezeMetrics GEX |
| `com.mario.quantlake.chain` | weekdays 08:20, 15:20, 16:00, 21:40 | SPX option chain snapshot |
| `com.mario.quantlake.maintain` | Sunday 03:15 | compact + vacuum |

Install one with:

```bash
cp launchd/com.mario.quantlake.maintain.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mario.quantlake.maintain.plist
```

Run maintenance while no live runner is writing: a concurrent merge makes
the compaction of that table fail (it is reported and retried on the next
run).

## Tests

```bash
poetry run pytest
```

No network: pure functions plus Delta round-trips in a temp directory.
