"""Reading real execution costs out of the desk's journal."""
import json

import pytest

from alphaquant.calibration.desk_fills import load_fills, summary


def _write(tmp_path, rows):
    p = tmp_path / "journal.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p


def fill(kind, oid, side="buy", usd=100.0, fee=0.0, dec=10.0, px=10.0):
    return {"kind": kind, "ts": "2026-10-10T00:05:00+00:00", "asset": "SOL", "side": side,
            "filled_usd": usd, "fee_usd": fee, "decision_px": dec, "fill_px": px, "exchange_oid": oid}


def test_paper_fills_are_left_out(tmp_path):
    """The desk's own model is not evidence about reality."""
    df = load_fills(_write(tmp_path, [fill("fill", None, fee=0.045)]))
    assert df.is_empty()


def test_the_exchange_fee_decides_maker_or_taker(tmp_path):
    df = load_fills(_write(tmp_path, [fill("fill_reconciled", "1", fee=0.015),
                                      fill("fill_reconciled", "2", fee=0.045)]))
    assert df["liquidity"].to_list() == ["maker", "taker"]
    assert df["fee_bps"].to_list() == pytest.approx([1.5, 4.5])


def test_an_order_is_counted_once_with_fee_and_slippage_from_the_right_record(tmp_path):
    """An IOC fill is journaled when it comes back and again when reconciled. The
    reconcile has no decision price and sets it to the fill price: its slippage
    is always zero and must not be the one used."""
    df = load_fills(_write(tmp_path, [
        fill("fill", "7", dec=10.0, px=10.01),
        fill("fill_reconciled", "7", fee=0.045, dec=10.01, px=10.01)]))
    assert df.height == 1
    assert df["fee_bps"].item() == pytest.approx(4.5)
    assert df["slippage_bps"].item() == pytest.approx(10.0)


def test_slippage_is_positive_when_it_costs(tmp_path):
    df = load_fills(_write(tmp_path, [fill("fill", "a", side="buy", px=10.01),      # paid up
                                      fill("fill", "b", side="sell", px=9.99)]))    # sold down
    assert df["slippage_bps"].to_list() == pytest.approx([10.0, 10.0])
    assert summary(df)["slip_bps_median"].item() == pytest.approx(10.0)
