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
desk ui                         # http://127.0.0.1:8765
```

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
└── ui/static/        single-page vanilla HTML/JS, no build step
```

The CLI (`desk run|status|kill|unlock|journal|universe`) still exists for scripts
and debugging; it drives the same files. Paper state lives in
`var/paper_account.json`, risk state in `var/risk_state.json`, UI settings in
`var/ui_settings.json`, the journal in `var/journal.jsonl`. Delete `var/` to start over.

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

Known phase-1 gaps on the live path: positions read back from the exchange have no
`strategy_id`/`opened_at` (a local ledger keyed on cloid is next), so the time stop
only works in paper mode; ALO orders that rest are cancelled at the next cycle rather
than tracked to fill. Mainnet asks you to type `MAINNET`; don't, yet.

## Phase 2 (not started)

`desk/research/`: Analyst → `Thesis`, Adversary → `Review`, both structured output,
every call logged. First use: a *veto* on reversal_v1 intents ("contrary catalyst in
the last 6h?"). Measured in shadow mode against the phase-1 baseline before it can
remove a single trade. Journal agent reads `var/journal.jsonl` and writes the daily
post-mortem. None of it can construct an `OrderIntent`; the boundary test makes sure.
