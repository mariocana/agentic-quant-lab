# ai-desk

A systematic trading desk on Hyperliquid, built so that LLM agents can be added
around it later without ever being able to move money on their own.

**Phase 1 (this):** deterministic core. No LLM anywhere. Strategy → rebalance →
risk engine → execution → journal. Paper adapter by default, testnet adapter opt-in.

```
desk/
├── schemas.py        contracts between modules (Thesis/Review for phase 2 already defined)
├── config.py         .env + config/limits.yaml
├── data/hl_market.py market data, always mainnet (testnet has no volume)
├── signals/          Strategy interface, reversal_v1, targets → OrderIntents
├── risk/             engine.py (pure functions) + state.py (day/peak/halt/kill switch)
├── execution/        paper.py (default), hyperliquid.py (API wallet, exchange-side stops)
├── journal/          append-only JSONL, one line per target/intent/verdict/fill/cycle
├── pm/notify.py      Telegram or stdout
├── research/         empty on purpose. Phase 2.
└── loop.py           one cycle
```

## Run

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"
cp .env.example .env            # optional for paper mode
.venv/bin/desk ui               # http://127.0.0.1:8765
```

`desk ui` runs a **preflight** before it opens the port: it byte-compiles every
module and parses the dashboard's script with node. There is no bundler here, so
this is the build step — without it a syntax error surfaces as a 500 on the first
request, or as a blank page served by a healthy-looking server. Both have happened.

| flag | |
|---|---|
| `--reload` | restart the desk whenever a source file changes. Development only: a restart can interrupt a running cycle. |
| `--no-preflight` | skip the compile/parse check. |
| `--port N` | default 8765. |

Python loads modules once, so a desk started *before* an edit keeps running the old
code — a fixed bug then looks unfixed. `/api/state` reports `stale_code` when a
source file is newer than the process: the dashboard shows a banner and the
acceptance script refuses to run until you restart.

The web UI is how the desk is operated. It shows equity (hero + curve), today's
P&L against the freeze line, drawdown against the halt line, gross/net exposure,
open positions with funding and time-stop age, the last cycle with every intent,
its verdict and the rules that fired, the risk limits as an editable form, the
strategy's current universe, an activity feed and the process logs. Actions: run
cycle, dry run, kill switch, unlock halt, close all, reset paper, switch
paper/live, and a built-in daily scheduler (no cron needed). Binds to localhost only.

```
├── ui/service.py     everything the UI can do, one object (adapter, lock, scheduler, log ring)
├── ui/server.py      FastAPI wrapper, /api/*
└── ui/static/        single-page vanilla HTML/JS, no bundler (see preflight above)
```

The CLI (`desk run|status|kill|unlock|journal|universe`) still exists for scripts
and debugging; it drives the same files. Paper state lives in
`var/paper_account.json`, risk state in `var/risk_state.json`, UI settings in
`var/ui_settings.json`, the journal in `var/journal.jsonl`. Delete `var/` to start over.

## Acceptance

The unit tests cover the pieces. This drives the running desk through its own API
and checks that the brakes work once they are all mounted together — it is what you
run before trusting the desk with money, and after any change under `risk/`.

```bash
.venv/bin/desk ui                          # terminal 1
.venv/bin/python scripts/acceptance.py     # terminal 2
```

| # | what it proves |
|---|---|
| 1 | the paper account resets to a known state |
| 2 | a dry run produces intents and executes **nothing** |
| 3 | a real cycle stays inside the per-asset cap and the leverage limit |
| 4 | a tiny per-asset cap rejects every opening intent — the limits actually bite |
| 5 | the kill switch blocks new risk and **still allows closing** |
| 6 | flatten leaves no position behind, not even dust |
| 7 | a daily-loss freeze refuses new risk |
| 8 | targets, intents, verdicts and fills all reach the journal |

Paper mode only — it refuses to run against a live account, and it refuses to run
against a stale process. It edits the paper account and `config/limits.yaml` while
it works and restores the limits afterwards, including after a failure.

It says nothing about whether the strategy makes money. It says that the risk
engine has the last word and that no path goes around it.

## Deploy (Railway)

The desk only trades when the process is alive. A laptop that sleeps misses cycles,
so once the paper track matters, run it on a platform.

1. **New project → Deploy from GitHub repo**, root directory `python/ai-desk`.
   `railway.json` points at the `Dockerfile`; nothing else to configure.
2. **Add a volume mounted at `/app/var`.** Without it every deploy wipes the paper
   account, the risk state and the journal.
3. **Set `DESK_PASSWORD`** to something long. The desk *refuses to start* on a
   non-loopback address without it — this dashboard closes positions, switches to
   live trading and edits risk limits, so it is never served open.
4. Turn the in-app scheduler on (Desk → Schedule). No cron, no launchd: the server
   is always up, so it runs its own cycles.

```bash
DESK_PASSWORD=... .venv/bin/python scripts/acceptance.py https://your-desk.up.railway.app
```

Run that once after the first deploy: it proves the brakes work on the box that
will actually be trading, not only on your laptop.

Health check is `/healthz`, the only route that needs no password. Logs in the
Railway dashboard; the desk's own log ring is in the UI.

**Before going live on a deployed desk:** the `HL_API_WALLET_KEY` env var lets that
box place orders (it cannot withdraw — that is the point of an API wallet). Anyone
with the password can also flip the desk to live from the UI. Use a password you do
not reuse, and keep the account small until the paper track has weeks behind it.

## The rules that matter

- **Strategies produce `TargetPosition`s. Nothing else.** They never see the account,
  never size against limits, never talk to execution.
- **`risk/engine.py` is the only thing that reads `config/limits.yaml`** and it can only
  reject or shrink. Closing risk is always allowed, even with the kill switch engaged.
- **Kill switch is a file** (`var/KILL`). `desk kill` / `desk unkill`. Any process, or you,
  can flip it without touching the running loop.
- **Halts need a human.** Daily loss beyond `daily_loss_flatten_pct` flattens and halts;
  drawdown beyond `max_drawdown_pct` halts. `desk unlock` clears it.
- **Stops live on the exchange.** The live adapter places a reduce-only trigger order
  after every fill; if this process dies the stop does not.
- **`tests/test_boundaries.py` enforces the import graph:** risk/execution/signals can
  never import an LLM client or `desk.research`; research can never import execution.

## Risk limits (`config/limits.yaml`)

| rule | default | effect |
|---|---|---|
| max notional per asset | 5% equity crypto, 2% HIP-3 | shrink |
| max gross leverage | 3x | shrink |
| max net beta | 100% equity | shrink (alts count as BTC) |
| daily loss | -3% freeze new risk, -5% flatten + halt | reject / flatten |
| max drawdown | -15% from peak | halt |
| liquidity | ≤10% of book within 10 bps, ≤0.1% of 24h volume | shrink |
| funding | paying > 0.01%/h: half; > 0.02%/h: reject | shrink / reject |
| min ticket | $15 | reject |
| time stop | horizon + 2h | close |

## Live (testnet)

1. Create an **API wallet** at app.hyperliquid.xyz/API (it can sign orders, not withdraw).
2. `.env`: `HL_TESTNET=1`, `HL_ACCOUNT_ADDRESS`, `HL_API_WALLET_KEY`.
3. In the UI, switch Mode to Live (testnet). Dry run first, then Run cycle.

Known phase-1 gaps on the live path, in the order they block things:

1. **No local position ledger.** Positions read back from the exchange carry no
   `strategy_id` / `opened_at`, so the time stop only works on paper and the
   rebalance cannot tell its own positions from anyone else's. Keyed on cloid, next.
2. **Fills are not reconciled.** Fees are estimated at 0.045% instead of read from
   `user_fills`, and an ALO order that rests is cancelled at the next cycle rather
   than followed to its fill.
3. **The live adapter has never seen a wallet.** It is written against the SDK
   signatures and nothing more. Testnet, dry run, then minimum size.

Mainnet asks you to type `MAINNET`; don't, yet.

## Phase 2 (not started)

`desk/research/`: Analyst → `Thesis`, Adversary → `Review`, both structured output,
every call logged. First use: a *veto* on reversal_v1 intents ("contrary catalyst in
the last 6h?"). Measured in shadow mode against the phase-1 baseline before it can
remove a single trade. Journal agent reads `var/journal.jsonl` and writes the daily
post-mortem. None of it can construct an `OrderIntent`; the boundary test makes sure.
