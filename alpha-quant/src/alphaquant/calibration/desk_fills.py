"""What execution really cost, read from the trading desk's journal.

A simulator is only worth what it reproduces. Before it judges a strategy nobody
has traded, it has to reproduce the costs of the trades the desk did make, so
this module turns the desk's journal into the numbers the cost model is fitted
on: fee and slippage per fill, split by how the order met the book.

Which records count:

  fill_reconciled   folded back from the exchange's own fill history. Carries
                    the real fee, so it is the only record that says whether a
                    fill was maker (1.5 bps on the base tier) or taker (4.5).
  fill              written by the desk when an IOC order comes back filled. Its
                    fee is a placeholder 0 until the reconcile, so its fee is
                    never used; its slippage against the decision price is.

When both exist for one order, the fee comes from the reconciled record and the
slippage from the immediate one: the reconcile rebuilds the fill from the
exchange history, which has no decision price, and sets it equal to the fill
price. Taking slippage from there would report every taker fill as free.

Paper fills (no exchange order id) are the desk's own model, not reality, and
are left out: fitting a model on its own output proves nothing.

What the journal cannot tell yet: how often a post-only order fills at all. An
order that rests and is cancelled leaves no record, so the fill rate of ALO
orders is unmeasured until the desk journals the orders it sends.
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

MAKER_FEE_BPS, TAKER_FEE_BPS = 1.5, 4.5          # Hyperliquid base tier, perps

FILLS_SCHEMA = {
    "ts": pl.String, "asset": pl.String, "side": pl.String, "liquidity": pl.String,
    "filled_usd": pl.Float64, "fee_bps": pl.Float64, "slippage_bps": pl.Float64,
}


def _liquidity(fee_bps: float) -> str:
    """Maker or taker, from the fee the exchange actually charged."""
    return "maker" if abs(fee_bps - MAKER_FEE_BPS) < abs(fee_bps - TAKER_FEE_BPS) else "taker"


def load_fills(journal: Path) -> pl.DataFrame:
    """One row per real fill. Slippage is signed so that positive always costs:
    a buy above the decision price, a sell below it."""
    rows = [json.loads(line) for line in Path(journal).read_text().splitlines() if line.strip()]
    real = [r for r in rows if r.get("kind") in ("fill", "fill_reconciled") and r.get("exchange_oid")]
    by_oid = {r["exchange_oid"]: r for r in real if r["kind"] == "fill_reconciled"}

    immediate = {r["exchange_oid"] for r in real if r["kind"] == "fill"}
    out = []
    for r in real:
        if r["kind"] == "fill_reconciled" and r["exchange_oid"] in immediate:
            continue                                  # its fee is joined onto the immediate record
        if not r.get("filled_usd") or not r.get("decision_px"):
            continue
        rec = by_oid.get(r["exchange_oid"]) if r["kind"] == "fill" else r
        fee_bps = rec["fee_usd"] / rec["filled_usd"] * 1e4 if rec else None
        sign = 1 if r["side"] == "buy" else -1
        out.append({
            "ts": r["ts"], "asset": r["asset"], "side": r["side"],
            # an IOC fill not yet reconciled is a taker by construction
            "liquidity": _liquidity(fee_bps) if fee_bps is not None else "taker",
            "filled_usd": float(r["filled_usd"]),
            "fee_bps": fee_bps if fee_bps is not None else TAKER_FEE_BPS,
            "slippage_bps": (r["fill_px"] / r["decision_px"] - 1) * 1e4 * sign,
        })
    return pl.DataFrame(out, schema=FILLS_SCHEMA)


def summary(fills: pl.DataFrame) -> pl.DataFrame:
    """Per liquidity: count, notional, fee and slippage quantiles in bps."""
    return (fills.group_by("liquidity").agg(
        pl.len().alias("n"),
        pl.col("filled_usd").sum().alias("notional_usd"),
        pl.col("fee_bps").median().alias("fee_bps_median"),
        pl.col("slippage_bps").median().alias("slip_bps_median"),
        pl.col("slippage_bps").quantile(0.9).alias("slip_bps_p90"),
        pl.col("slippage_bps").mean().alias("slip_bps_mean"),
    ).sort("liquidity"))
