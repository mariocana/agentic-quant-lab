"""Analysis orchestration for the COT desk.

Ported from cot-analyzer's core.py. Positioning now comes from the
quantlake gold table gold/cot_positioning/1w (see store.py) instead of
Postgres: week-over-week changes and z26/z52 are precomputed there on
prior weeks only, so build_snapshots just maps rows. Pair biases,
classification, top-3 selection and the AI prompts are unchanged.

Functions:
  run_analysis(as_of_date=None) -> dict
      Full analysis: currencies, pairs, matrices, single assets, top setups.
  history_for(ticker) -> dict
      Historical series for one instrument (/api/history/<ticker>).
  ai_top3_overview / ai_asset_overview
      On-demand Claude review (needs ANTHROPIC_API_KEY in .env).
"""

import os
import time
from dataclasses import dataclass, field
from datetime import date

import store
from instruments import INSTRUMENTS


# ---------------------------------------------------------------------------
# Data model (in-memory representation, like the old CotData)
# ---------------------------------------------------------------------------
@dataclass
class AssetSnapshot:
    """Latest weekly snapshot for one instrument, with derived metrics."""
    ticker: str
    name: str
    category: str
    report_date: date
    # Current week
    nc_long: int
    nc_short: int
    open_interest: int
    # Derived from current week
    @property
    def net(self) -> int:
        return self.nc_long - self.nc_short
    @property
    def net_pct_oi(self) -> float:
        return 100 * self.net / self.open_interest if self.open_interest else 0.0
    # Previous week (filled in by build_snapshots)
    prev_nc_long: int = 0
    prev_nc_short: int = 0
    # Derived: weekly changes
    @property
    def nc_long_chg(self) -> int:
        return self.nc_long - self.prev_nc_long
    @property
    def nc_short_chg(self) -> int:
        return self.nc_short - self.prev_nc_short
    @property
    def net_chg(self) -> int:
        return self.nc_long_chg - self.nc_short_chg
    # Historical context (z-score)
    z26: float | None = None
    pct_rank_26w: float | None = None
    z52: float | None = None


# ---------------------------------------------------------------------------
# Build snapshots from gold
# ---------------------------------------------------------------------------
def build_snapshots(as_of_date: date | None = None) -> dict[str, AssetSnapshot]:
    """One snapshot per instrument from its latest gold row.

    With `as_of_date`, the row is the latest with report_date <= as_of_date.
    Its z-scores were computed on the weeks before it only, so backtest mode
    stays free of look-ahead exactly as before.
    """
    snapshots: dict[str, AssetSnapshot] = {}
    rows = store.latest_rows(as_of_date)
    for ticker, inst in INSTRUMENTS.items():
        r = rows.get(ticker)
        if r is None:
            continue
        snapshots[ticker] = AssetSnapshot(
            ticker=ticker,
            name=inst.name,
            category=inst.category,
            report_date=r["report_date"],
            nc_long=r["nc_long"],
            nc_short=r["nc_short"],
            open_interest=r["open_interest"],
            # First week has no change: prev = current, as in cot-analyzer.
            prev_nc_long=r["nc_long"] - (r["nc_long_chg"] or 0),
            prev_nc_short=r["nc_short"] - (r["nc_short_chg"] or 0),
            z26=r["z26"],
            pct_rank_26w=r["pct_rank_26"],
            z52=r["z52"],
        )
    return snapshots


# ---------------------------------------------------------------------------
# FX pair analysis
# ---------------------------------------------------------------------------
@dataclass
class PairBias:
    pair: str           # e.g. "EUR/JPY"
    net_diff: int       # net(base) - net(quote)
    chg_diff: int       # net_chg(base) - net_chg(quote)

    @property
    def long_bias_label(self) -> str:
        if self.net_diff > 80_000:   return "🟢🟢 BULL strong"
        if self.net_diff > 25_000:   return "🟢 Bull"
        if self.net_diff < -80_000:  return "🔴🔴 BEAR strong"
        if self.net_diff < -25_000:  return "🔴 Bear"
        return "⚪ Neutral"

    @property
    def momentum_label(self) -> str:
        if self.chg_diff > 15_000:   return "↑↑ bull accelerating"
        if self.chg_diff > 3_000:    return "↑ toward bull"
        if self.chg_diff < -15_000:  return "↓↓ bear accelerating"
        if self.chg_diff < -3_000:   return "↓ toward bear"
        return "→ stable"

    @property
    def alignment(self) -> str:
        long_pos = self.net_diff > 25_000
        long_neg = self.net_diff < -25_000
        mom_pos  = self.chg_diff > 3_000
        mom_neg  = self.chg_diff < -3_000
        if (long_pos and mom_pos) or (long_neg and mom_neg):
            return "✓ aligned"
        if (long_pos and mom_neg) or (long_neg and mom_pos):
            return "⚠ divergent"
        return "·"

    @property
    def is_clean_setup(self) -> bool:
        return self.alignment == "✓ aligned" and abs(self.net_diff) > 25_000


def compute_all_pairs(currencies: dict[str, AssetSnapshot]) -> list[PairBias]:
    """Build all unique FX cross-pairs from the 8 currencies."""
    fx_priority = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"]
    ordered = [c for c in fx_priority if c in currencies]
    pairs: list[PairBias] = []
    for i, b in enumerate(ordered):
        base = currencies[b]
        for q in ordered[i+1:]:
            quote = currencies[q]
            pairs.append(PairBias(
                pair=f"{b}/{q}",
                net_diff=base.net - quote.net,
                chg_diff=base.net_chg - quote.net_chg,
            ))
    return pairs


# ---------------------------------------------------------------------------
# Single-asset classification
# ---------------------------------------------------------------------------
def classify_single_asset(a: AssetSnapshot) -> tuple[str, str, bool]:
    """Return (bias_label, momentum_label, is_clean_setup) for one asset.
    Thresholds based on net%OI so different OI sizes are comparable."""
    pct = a.net_pct_oi
    if pct > 25:    bias = "🟢🟢 BULL extreme"
    elif pct > 10:  bias = "🟢 Bull"
    elif pct < -25: bias = "🔴🔴 BEAR extreme"
    elif pct < -10: bias = "🔴 Bear"
    else:           bias = "⚪ Neutral"

    chg_pct = 100 * a.net_chg / a.open_interest if a.open_interest else 0
    if chg_pct > 2:      momentum = "↑↑ bull accelerating"
    elif chg_pct > 0.5:  momentum = "↑ toward bull"
    elif chg_pct < -2:   momentum = "↓↓ bear accelerating"
    elif chg_pct < -0.5: momentum = "↓ toward bear"
    else:                momentum = "→ stable"

    is_clean = (
        (pct > 10 and chg_pct > 0.5) or
        (pct < -10 and chg_pct < -0.5)
    )
    return bias, momentum, is_clean


# ---------------------------------------------------------------------------
# Top setup selection
# ---------------------------------------------------------------------------
@dataclass
class Setup:
    label: str           # "EUR/JPY" or "GC (GOLD)"
    asset_type: str      # "FX_PAIR" or "SINGLE"
    bias_label: str
    momentum_label: str
    net_value: int
    chg_value: int
    strength_score: float
    z26: float | None = None
    z26_quote: float | None = None
    details: dict = field(default_factory=dict)


def _score_pair(p: PairBias) -> float:
    bias_score = min(abs(p.net_diff) / 2000, 100)
    mom_score  = min(abs(p.chg_diff) / 300, 100)
    return bias_score * 0.7 + mom_score * 0.3


def _score_single(a: AssetSnapshot) -> float:
    bias_score = min(abs(a.net_pct_oi) * 2.5, 100)
    chg_pct = abs(a.net_chg) / a.open_interest * 100 if a.open_interest else 0
    mom_score = min(chg_pct * 33, 100)
    return bias_score * 0.7 + mom_score * 0.3


def select_top_3_setups(pairs: list[PairBias],
                        assets: dict[str, AssetSnapshot],
                        currencies: dict[str, AssetSnapshot]) -> list[Setup]:
    """Return the top 3 setups by composite score (bias + momentum + z bonus)."""
    setups: list[Setup] = []

    for p in pairs:
        if not p.is_clean_setup:
            continue
        base_code, quote_code = p.pair.split("/")
        base = currencies[base_code]
        quote = currencies[quote_code]
        score = _score_pair(p)
        # Z bonus
        z_bonus = 0.0
        if base.z26 is not None and abs(base.z26) > 1.5:
            z_bonus += min(abs(base.z26) * 5, 15)
        if quote.z26 is not None and abs(quote.z26) > 1.5:
            z_bonus += min(abs(quote.z26) * 5, 15)
        setups.append(Setup(
            label=p.pair, asset_type="FX_PAIR",
            bias_label=p.long_bias_label, momentum_label=p.momentum_label,
            net_value=p.net_diff, chg_value=p.chg_diff,
            strength_score=score + z_bonus,
            z26=base.z26, z26_quote=quote.z26,
            details={
                "pair": p.pair,
                "net_diff": p.net_diff, "chg_diff": p.chg_diff,
                "base": {
                    "code": base.ticker, "long": base.nc_long, "short": base.nc_short,
                    "net": base.net, "net_chg": base.net_chg,
                    "z26": round(base.z26, 2) if base.z26 is not None else None,
                    "pct_rank_26w": round(base.pct_rank_26w, 0) if base.pct_rank_26w is not None else None,
                },
                "quote": {
                    "code": quote.ticker, "long": quote.nc_long, "short": quote.nc_short,
                    "net": quote.net, "net_chg": quote.net_chg,
                    "z26": round(quote.z26, 2) if quote.z26 is not None else None,
                    "pct_rank_26w": round(quote.pct_rank_26w, 0) if quote.pct_rank_26w is not None else None,
                },
            }
        ))

    for a in assets.values():
        bias, momentum, is_clean = classify_single_asset(a)
        if not is_clean:
            continue
        score = _score_single(a)
        z_bonus = 0.0
        if a.z26 is not None and abs(a.z26) > 1.5:
            z_bonus = min(abs(a.z26) * 5, 15)
        setups.append(Setup(
            label=f"{a.ticker} ({a.name})", asset_type="SINGLE",
            bias_label=bias, momentum_label=momentum,
            net_value=a.net, chg_value=a.net_chg,
            strength_score=score + z_bonus,
            z26=a.z26,
            details={
                "code": a.ticker, "name": a.name, "category": a.category,
                "long": a.nc_long, "short": a.nc_short,
                "net": a.net, "net_pct_oi": round(a.net_pct_oi, 2),
                "long_chg": a.nc_long_chg, "short_chg": a.nc_short_chg,
                "net_chg": a.net_chg, "open_interest": a.open_interest,
                "z26": round(a.z26, 2) if a.z26 is not None else None,
                "z52": round(a.z52, 2) if a.z52 is not None else None,
                "pct_rank_26w": round(a.pct_rank_26w, 0) if a.pct_rank_26w is not None else None,
            }
        ))

    setups.sort(key=lambda x: x.strength_score, reverse=True)
    return setups[:3]


# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------
def _currency_row(c: AssetSnapshot) -> dict:
    return {
        "code": c.ticker,
        "name": c.name,
        "report_date": c.report_date.isoformat(),
        "long": c.nc_long,
        "short": c.nc_short,
        "net": c.net,
        "long_chg": c.nc_long_chg,
        "short_chg": c.nc_short_chg,
        "net_chg": c.net_chg,
        "z26": round(c.z26, 2) if c.z26 is not None else None,
        "pct_rank_26w": round(c.pct_rank_26w, 0) if c.pct_rank_26w is not None else None,
        "z52": round(c.z52, 2) if c.z52 is not None else None,
    }


def _asset_row(a: AssetSnapshot) -> dict:
    bias, momentum, is_clean = classify_single_asset(a)
    return {
        "code": a.ticker,
        "name": a.name,
        "category": a.category,
        "report_date": a.report_date.isoformat(),
        "net": a.net,
        "net_pct_oi": round(a.net_pct_oi, 1),
        "net_chg": a.net_chg,
        "open_interest": a.open_interest,
        "bias": bias,
        "momentum": momentum,
        "is_clean": is_clean,
        "z26": round(a.z26, 2) if a.z26 is not None else None,
        "pct_rank_26w": round(a.pct_rank_26w, 0) if a.pct_rank_26w is not None else None,
        "z52": round(a.z52, 2) if a.z52 is not None else None,
    }


def _pair_row(p: PairBias) -> dict:
    return {
        "pair": p.pair,
        "net_diff": p.net_diff,
        "chg_diff": p.chg_diff,
        "bias": p.long_bias_label,
        "momentum": p.momentum_label,
        "alignment": p.alignment,
        "is_clean": p.is_clean_setup,
    }


# ---------------------------------------------------------------------------
# AI review (unchanged logic, prompt stays in Italian as before)
# ---------------------------------------------------------------------------
# Default: latest Opus. Override with COT_AI_MODEL in .env.
AI_MODEL = os.environ.get("COT_AI_MODEL", "claude-opus-5-5")


def _build_ai_prompt(top_setups: list[Setup], report_date: str,
                     is_historical: bool = False) -> str:
    import json as _json
    setups_json = _json.dumps(
        [{"label": s.label, "type": s.asset_type, "bias": s.bias_label,
          "momentum": s.momentum_label, **s.details} for s in top_setups],
        indent=2, ensure_ascii=False
    )

    context_note = ""
    if is_historical:
        context_note = (
            f"\n\n⚠ NOTA IMPORTANTE: Questo è un report STORICO al {report_date}, "
            f"non l'ultimo report disponibile. L'utente sta facendo backtest. "
            f"Analizza il posizionamento come se fossi a quella data, SENZA "
            f"usare informazioni successive. Non dire mai 'come sappiamo oggi' "
            f"o riferimenti a eventi posteriori al {report_date}. "
            f"Le note operative sono illustrative, non operative.\n"
        )

    return f"""Sei un analista esperto di posizionamento COT (Commitment of Traders) che assiste un trader prop swing. Stai facendo da sounding board critico, NON da advisor.{context_note}

DATI: COT Legacy Report Non-Commercial al {report_date}, i 3 setup con bias di lungo + momentum settimanale allineati. Ogni setup include lo z-score a 26 settimane (z26) e il percentile rank, calcolati sui dati storici ufficiali CFTC (sulle 26 settimane PRECEDENTI questo report):

```json
{setups_json}
```

INTERPRETAZIONE Z-SCORE:
- |z26| > 2.0  → ESTREMO statistico (top/bottom ~2.5% degli ultimi 6 mesi)
- |z26| > 1.5  → stretched, attenzione a unwind
- |z26| > 1.0  → posizionamento sopra la media
- |z26| < 1.0  → nella norma

Per OGNUNO dei 3 setup, fornisci un'analisi di ~180 parole strutturata così:

**[NOME SETUP]** — Bias COT: [direzione]

1. **Cosa dice il posizionamento**: usa z26 e percentile rank per quantificare quanto è affollato il trade.
2. **Cosa dice il momentum**: ΔNet conferma o smentisce?
3. **Rischi e blind spot**: affollamento, divergenze, eventi macro, bias cognitivi.
4. **Note operative**: NON dare entry/stop/target. Cosa cercare sul grafico, orizzonte temporale.

Tono: diretto, professionale, critico. Devil's advocate da collega esperto.

Chiudi con ~100 parole di **CONTESTO INCROCIATO** — tema macro, coerenza interna, quale dei 3 è più solido e quale più rischioso.
"""


def _call_claude(prompt: str) -> tuple[str | None, str]:
    """Return (text, model that answered). Raises on API errors.

    Server-side fallback ("default") re-runs a safety-classifier refusal on
    the model Anthropic recommends for that category, inside the same call.
    """
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    response = client.beta.messages.create(
        model=AI_MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise RuntimeError(f"Claude declined the request (category: {category})")
    text = "\n".join(b.text for b in response.content if b.type == "text").strip()
    return text or None, response.model


# ---------------------------------------------------------------------------
# Public API: run_analysis (gold-backed, fast)
# ---------------------------------------------------------------------------
def run_analysis(progress=None, as_of_date: date | None = None) -> dict:
    """Run the full analysis from gold/cot_positioning. No network, no AI.

    The AI overview is now a separate, on-demand step (see ai_top3_overview
    and ai_asset_overview). This function only computes the positioning data.

    If `as_of_date` is given, the analysis reflects positioning as of that
    specific past report date — useful for backtesting. Z-scores and momentum
    are computed using only data ≤ as_of_date (no look-ahead).

    Returns a JSON-serializable dict with an `is_historical` flag when
    as_of_date is set.
    """
    def log(msg):
        if progress:
            progress(msg)

    if as_of_date:
        log(f"Loading positioning data as of {as_of_date}...")
    else:
        log("Loading latest positioning data from gold...")
    snapshots = build_snapshots(as_of_date=as_of_date)

    if not snapshots:
        return {
            "ok": False,
            "error": ("No COT data in quantlake yet. Hit the SYNC button first "
                      "to pull it from the CFTC API.") if as_of_date is None
                     else f"No data available on or before {as_of_date}.",
        }

    # Split FX from single assets
    currencies = {t: s for t, s in snapshots.items() if s.category == "FX"}
    assets     = {t: s for t, s in snapshots.items() if s.category != "FX"}

    log("Computing pair biases...")
    pairs = compute_all_pairs(currencies)

    # Build cross-pair matrices (in thousands of contracts)
    matrix_codes = [c for c in ["EUR", "GBP", "AUD", "NZD", "CAD", "CHF", "JPY", "USD"]
                    if c in currencies]
    bias_matrix, mom_matrix = [], []
    for b in matrix_codes:
        bias_row = {"base": b, "cells": {}}
        mom_row  = {"base": b, "cells": {}}
        for q in matrix_codes:
            if b == q:
                bias_row["cells"][q] = None
                mom_row["cells"][q]  = None
            else:
                bias_row["cells"][q] = round((currencies[b].net - currencies[q].net) / 1000, 1)
                mom_row["cells"][q]  = round((currencies[b].net_chg - currencies[q].net_chg) / 1000, 1)
        bias_matrix.append(bias_row)
        mom_matrix.append(mom_row)

    # Sort outputs
    ccy_rows = sorted([_currency_row(c) for c in currencies.values()],
                     key=lambda x: x["net"], reverse=True)
    pair_rows = sorted([_pair_row(p) for p in pairs],
                      key=lambda x: abs(x["net_diff"]), reverse=True)
    asset_rows = sorted([_asset_row(a) for a in assets.values()],
                       key=lambda x: (x["category"], -x["net_pct_oi"]))

    # Top 3
    top = select_top_3_setups(pairs, assets, currencies)
    top_setups = [{
        "label": s.label, "type": s.asset_type,
        "bias": s.bias_label, "momentum": s.momentum_label,
        "net_value": s.net_value, "chg_value": s.chg_value,
        "score": round(s.strength_score, 1),
        "z26": round(s.z26, 2) if s.z26 is not None else None,
    } for s in top]

    # Report date = max date across snapshots
    report_date = max(s.report_date for s in snapshots.values())

    log("Done.")
    return {
        "ok": True,
        "report_date": report_date.isoformat(),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_historical": as_of_date is not None,
        "requested_as_of": as_of_date.isoformat() if as_of_date else None,
        "currencies": ccy_rows,
        "pairs": pair_rows,
        "bias_matrix": bias_matrix,
        "momentum_matrix": mom_matrix,
        "matrix_codes": matrix_codes,
        "assets": asset_rows,
        "top_setups": top_setups,
        "counts": {
            "currencies": len(currencies),
            "assets":     len(assets),
            "pairs":      len(pairs),
        },
    }


# ---------------------------------------------------------------------------
# Public API: history_for (for the /history/<asset> endpoint)
# ---------------------------------------------------------------------------
def history_for(ticker: str) -> dict:
    """Return the full historical series for one instrument, formatted for
    the chart frontend."""
    if ticker not in INSTRUMENTS:
        return {"ok": False, "error": f"Unknown instrument: {ticker}"}

    inst = INSTRUMENTS[ticker]
    rows = store.history(ticker)
    if not rows:
        return {
            "ok": False,
            "error": f"No data for {ticker}. Hit the SYNC button first.",
        }

    series = [{
        "date":          r["report_date"].isoformat(),
        "nc_long":       r["nc_long"],
        "nc_short":      r["nc_short"],
        "net":           r["nc_long"] - r["nc_short"],
        "open_interest": r["open_interest"],
    } for r in rows]

    return {
        "ok": True,
        "ticker": ticker,
        "name": inst.name,
        "category": inst.category,
        "n_weeks": len(series),
        "oldest": series[0]["date"],
        "newest": series[-1]["date"],
        "series": series,
    }


# ---------------------------------------------------------------------------
# On-demand AI overviews (separate from run_analysis)
# ---------------------------------------------------------------------------
def ai_top3_overview(as_of_date: date | None = None) -> dict:
    """Generate the AI overview of the top-3 setups, on demand.

    Rebuilds the snapshots (cheap, from gold), selects the top-3, and asks
    Claude for a critical review. Returns {status, text, model}.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"status": "no_key", "text": None, "model": None}

    snapshots = build_snapshots(as_of_date=as_of_date)
    if not snapshots:
        return {"status": "error", "text": "No COT data yet.", "model": None}

    currencies = {t: s for t, s in snapshots.items() if s.category == "FX"}
    assets     = {t: s for t, s in snapshots.items() if s.category != "FX"}
    pairs = compute_all_pairs(currencies)
    top = select_top_3_setups(pairs, assets, currencies)

    if not top:
        return {"status": "no_setups", "text": None, "model": None}

    report_date = max(s.report_date for s in snapshots.values())
    try:
        prompt = _build_ai_prompt(top, report_date.isoformat(),
                                  is_historical=(as_of_date is not None))
        text, model = _call_claude(prompt)
        if text:
            return {"status": "ok", "text": text, "model": model}
        return {"status": "error", "text": "Empty AI response.", "model": None}
    except Exception as e:
        return {"status": "error", "text": str(e), "model": None}


def _build_asset_prompt(snap: AssetSnapshot, recent_history: list[dict],
                        report_date: str, is_historical: bool = False) -> str:
    """Build the prompt for a single-asset COT overview.

    Structured so that adding external macro context later is just a matter
    of appending another data block — the COT analysis stays self-contained.
    """
    import json as _json

    # Compact recent net history (last ~13 weeks) for trend context
    hist_compact = [
        {"date": r["date"], "net": r["net"], "oi": r["open_interest"]}
        for r in recent_history[-13:]
    ]

    bias, momentum, _ = classify_single_asset(snap)
    data = {
        "ticker": snap.ticker,
        "name": snap.name,
        "category": snap.category,
        "report_date": report_date,
        "current": {
            "nc_long": snap.nc_long,
            "nc_short": snap.nc_short,
            "net": snap.net,
            "net_pct_oi": round(snap.net_pct_oi, 2),
            "open_interest": snap.open_interest,
        },
        "weekly_change": {
            "long_chg": snap.nc_long_chg,
            "short_chg": snap.nc_short_chg,
            "net_chg": snap.net_chg,
        },
        "historical_context": {
            "z26": round(snap.z26, 2) if snap.z26 is not None else None,
            "z52": round(snap.z52, 2) if snap.z52 is not None else None,
            "pct_rank_26w": round(snap.pct_rank_26w, 0) if snap.pct_rank_26w is not None else None,
        },
        "bias_label": bias,
        "momentum_label": momentum,
        "recent_net_history_13w": hist_compact,
    }
    data_json = _json.dumps(data, indent=2, ensure_ascii=False)

    context_note = ""
    if is_historical:
        context_note = (
            f"\n\n⚠ NOTA: Questo è un report STORICO al {report_date} (backtest). "
            f"Analizza come se fossi a quella data, senza informazioni successive.\n"
        )

    return f"""Sei un analista esperto di posizionamento COT (Commitment of Traders) che assiste un trader prop swing. Stai facendo da sounding board critico, NON da advisor.{context_note}

L'utente vuole un overview approfondito di UN SINGOLO strumento basato sui dati COT Non-Commercial (speculatori). Ecco i dati ufficiali CFTC al {report_date}:

```json
{data_json}
```

INTERPRETAZIONE Z-SCORE:
- |z26| > 2.0  → ESTREMO statistico (top/bottom ~2.5% degli ultimi 6 mesi)
- |z26| > 1.5  → stretched, attenzione a unwind
- |z26| > 1.0  → posizionamento sopra la media
- |z26| < 1.0  → nella norma

Fornisci un overview di ~300 parole strutturato così:

**{snap.name} — COT Overview**

1. **Posizionamento attuale**: cosa dicono net e net%OI? Usa z26/z52 e il percentile rank per quantificare quanto è affollato/estremo il posizionamento rispetto alla storia recente. Sii preciso sui numeri.

2. **Dinamica recente**: leggi la `recent_net_history_13w` e descrivi il trend delle ultime settimane. Il net sta crescendo, calando, invertendo? Il momentum settimanale (net_chg) conferma o contraddice il trend?

3. **Open interest**: cosa segnala l'evoluzione dell'OI? OI in crescita + net in crescita = convinzione. OI in calo + net che si riduce = chiusura posizioni / disinteresse.

4. **Rischi e scenari**: se il posizionamento è estremo, qual è il rischio di unwind? Quali sono i bias cognitivi tipici su questo strumento? Cosa cercheresti sul grafico prezzo per validare o invalidare la lettura COT?

5. **Sintesi**: in 2-3 frasi, qual è il quadro COT complessivo di questo strumento adesso?

Tono: diretto, professionale, critico. Niente disclaimer generici, niente "consulta un advisor". Devil's advocate da collega esperto. NON dare entry/stop/target.

Nota: questo overview è basato SOLO sui dati COT. Non hai accesso a prezzi di mercato, notizie o dati macro live — non inventarli. Se un giudizio richiederebbe dati di prezzo che non hai, dillo esplicitamente.
"""


def ai_asset_overview(ticker: str, as_of_date: date | None = None) -> dict:
    """Generate an AI overview of a single instrument's COT positioning.

    COT-only for now. Designed so external macro context can be added later
    without restructuring. Returns {status, text, model, ticker, name}.
    """
    ticker = ticker.upper()
    if ticker not in INSTRUMENTS:
        return {"status": "error", "text": f"Unknown instrument: {ticker}",
                "model": None}

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"status": "no_key", "text": None, "model": None,
                "ticker": ticker, "name": INSTRUMENTS[ticker].name}

    snapshots = build_snapshots(as_of_date=as_of_date)
    if ticker not in snapshots:
        return {"status": "error",
                "text": f"No data for {ticker} on or before the selected date.",
                "model": None}

    snap = snapshots[ticker]

    # Recent history for trend context (respecting as_of_date if backtest)
    rows = store.history(ticker, as_of=as_of_date, limit_weeks=13)
    recent_history = [{
        "date": r["report_date"].isoformat(),
        "net": r["nc_long"] - r["nc_short"],
        "open_interest": r["open_interest"],
    } for r in rows]

    report_date = snap.report_date.isoformat()
    try:
        prompt = _build_asset_prompt(snap, recent_history, report_date,
                                     is_historical=(as_of_date is not None))
        text, model = _call_claude(prompt)
        if text:
            return {"status": "ok", "text": text, "model": model,
                    "ticker": ticker, "name": snap.name}
        return {"status": "error", "text": "Empty AI response.", "model": None}
    except Exception as e:
        return {"status": "error", "text": str(e), "model": None}
