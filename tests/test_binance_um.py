"""Binance USDⓈ-M connectors, funding silver and historical/binance_um.py (HTTP mocked)."""
import importlib.util
import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import polars as pl
import pytest

import quantlake.bronze.connectors.binance_spot_bulk as bulk_mod
import quantlake.bronze.connectors.binance_spot_rest as rest_mod
import quantlake.bronze.connectors.binance_um as um
import quantlake.silver.ingest as silver
from helpers import utc
from quantlake.bronze.connectors.binance_spot_bulk import parse_kline_zip
from quantlake.silver.funding import SCHEMA as FUNDING_SCHEMA, clean_funding
from quantlake.storage import read_symbol

MS = 1000


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * MS)


def _kline_row(t: datetime, unit: int = MS) -> list:
    o = int(t.timestamp() * unit)
    return [o, "100.0", "101.0", "99.0", "100.5", "2.5", o + 60 * unit - 1, "250.0", 10, "1.0", "100.0", "0"]


def _zip(rows: list[list], header: bool) -> bytes:
    lines = (["open_time,open,high,low,close,volume,close_time,quote_volume,count,"
              "taker_buy_volume,taker_buy_quote_volume,ignore"] if header else [])
    lines += [",".join(str(v) for v in r) for r in rows]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("BTCUSDT-1m-2024-01.csv", "\n".join(lines) + "\n")
    return buf.getvalue()


def _mock_client(monkeypatch, module, handler):
    real = httpx.Client
    monkeypatch.setattr(module.httpx, "Client",
                        lambda *a, **k: real(transport=httpx.MockTransport(handler), timeout=k.get("timeout")))


# ── kline ZIPs ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("header", [False, True])  # spot: no header, futures: header
def test_parse_kline_zip(header):
    t0 = utc(2024, 1, 1)
    df = parse_kline_zip(_zip([_kline_row(t0), _kline_row(t0 + timedelta(minutes=1))], header))
    assert df.columns == ["timestamp", "timestamp_close", "open", "high", "low", "close", "volume"]
    assert df["timestamp"].to_list() == [t0, t0 + timedelta(minutes=1)]
    assert df["timestamp_close"][0] == t0 + timedelta(seconds=59, milliseconds=999)
    assert df.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert df["volume"].to_list() == [2.5, 2.5]


def test_parse_kline_zip_microseconds():
    t0 = utc(2025, 1, 1)
    df = parse_kline_zip(_zip([_kline_row(t0, unit=1_000_000)], header=False))
    assert df["timestamp"].to_list() == [t0]


def test_um_bulk_uses_futures_archive_and_skips_missing_months(monkeypatch):
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(str(req.url))
        if "2024-02" in str(req.url):
            return httpx.Response(404)
        return httpx.Response(200, content=_zip([_kline_row(utc(2024, 1, 31, 23, 59))], header=True))

    _mock_client(monkeypatch, bulk_mod, handler)
    df = um.BinanceUMOHLCVBulkConnector().fetch("BTCUSDT", utc(2024, 1, 1), utc(2024, 2, 29))
    assert seen[0] == "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip"
    assert len(seen) == 2
    assert df["timestamp"].to_list() == [utc(2024, 1, 31, 23, 59)]


def test_um_rest_uses_fapi(monkeypatch):
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req.url)
        start, end = int(req.url.params["startTime"]), int(req.url.params["endTime"])
        minutes = [utc(2024, 1, 1) + timedelta(minutes=i) for i in range(10)]
        return httpx.Response(200, json=[_kline_row(t) for t in minutes if start <= _ms(t) <= end])

    _mock_client(monkeypatch, rest_mod, handler)
    df = um.BinanceUMOHLCVRestConnector().fetch("BTCUSDT", utc(2024, 1, 1), utc(2024, 1, 1, 0, 2, 59))
    assert seen[0].host == "fapi.binance.com" and seen[0].path == "/fapi/v1/klines"
    assert seen[0].params["limit"] == "1500"
    assert df.height == 3


# ── funding ────────────────────────────────────────────────────────────────

def _funding_rows(n: int, start: datetime, offset_ms: int = 8) -> list[dict]:
    return [
        {"symbol": "BTCUSDT", "fundingTime": _ms(start + timedelta(hours=8 * i)) + offset_ms,
         "fundingRate": "0.00010000", "markPrice": "" if i == 0 else "42000.5"}
        for i in range(n)
    ]


def test_funding_paginates_until_a_short_page(monkeypatch):
    calls = []
    first = _funding_rows(1000, utc(2020, 1, 1))
    second = _funding_rows(3, utc(2020, 1, 1) + timedelta(hours=8 * 1000))

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(dict(req.url.params))
        return httpx.Response(200, json=first if len(calls) == 1 else second)

    _mock_client(monkeypatch, um, handler)
    df = um.BinanceUMFundingRateConnector(pause_s=0).fetch("BTCUSDT", utc(2020, 1, 1), utc(2021, 1, 1))
    assert len(calls) == 2
    assert int(calls[1]["startTime"]) == first[-1]["fundingTime"] + 1
    assert df.height == 1003
    assert dict(df.schema) == um.FUNDING_SCHEMA
    assert df["mark_price"][0] is None and df["mark_price"][1] == 42000.5
    assert df["timestamp"][0] == utc(2020, 1, 1) + timedelta(milliseconds=8)  # bronze keeps it as published


def test_clean_funding_truncates_dedupes_and_keeps_nan():
    t = utc(2020, 1, 1)
    df = pl.DataFrame({
        "timestamp": pl.Series([t + timedelta(milliseconds=8), t + timedelta(milliseconds=3), t + timedelta(hours=8)],
                               dtype=pl.Datetime("us", "UTC")),
        "funding_rate": [0.0001, 0.0002, None],
        "mark_price": [1.0, 2.0, 3.0],
        "symbol": ["BTCUSDT"] * 3,
        "ingested_at": pl.Series([t, t + timedelta(days=1), t], dtype=pl.Datetime("us", "UTC")),
        "year": pl.Series([2020] * 3, dtype=pl.Int32),
        "month": pl.Series([1] * 3, dtype=pl.Int8),
    })
    out = clean_funding(df)
    assert dict(out.schema) == FUNDING_SCHEMA
    assert out["timestamp"].to_list() == [t, t + timedelta(hours=8)]
    assert out["funding_rate"][0] == 0.0002  # most recently ingested wins
    assert out["funding_rate"][1] != out["funding_rate"][1]  # NaN, row kept


# ── historical/binance_um.py ───────────────────────────────────────────────

def test_binance_um_script_fills_bronze_and_silver(lake, monkeypatch):
    t0 = utc(2024, 1, 31, 23, 58)

    def bulk_fetch(self, symbol, start, end):
        rows = [_kline_row(t0 + timedelta(minutes=i)) for i in range(2)]
        df = parse_kline_zip(_zip(rows, header=True))
        # one shifted open time, like the old spot archives
        return df.with_columns(pl.when(pl.int_range(pl.len()) == 1)
                               .then(pl.col("timestamp") + timedelta(seconds=20)).otherwise(pl.col("timestamp")))

    rest_calls = []

    def rest_fetch(self, symbol, start, end):
        rest_calls.append((start, end))
        return parse_kline_zip(_zip([_kline_row(utc(2024, 2, 1, 0, 0))], header=False))

    def funding_fetch(self, symbol, start, end):
        return um.parse_funding(_funding_rows(3, utc(2024, 1, 31)))

    monkeypatch.setattr(um.BinanceUMOHLCVBulkConnector, "fetch", bulk_fetch)
    monkeypatch.setattr(um.BinanceUMOHLCVRestConnector, "fetch", rest_fetch)
    monkeypatch.setattr(um.BinanceUMFundingRateConnector, "fetch", funding_fetch)

    path = Path(__file__).parents[1] / "applications" / "historical" / "binance_um.py"
    spec = importlib.util.spec_from_file_location("binance_um_script", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    now = utc(2024, 2, 1, 0, 1, 30)
    mod.ingest_ohlcv("BTCUSDT", now)
    mod.ingest_funding("BTCUSDT", now)

    # REST resumes at the minute after the last bulk bar (raw 23:59:20 → 00:00)
    # and stops before the minute still open
    assert rest_calls == [(utc(2024, 2, 1, 0, 0), utc(2024, 2, 1, 0, 1) - timedelta(milliseconds=1))]
    s = read_symbol(str(silver.SILVER_ROOT / "binance_um_ohlcv"), "BTCUSDT").sort("timestamp")
    assert s["timestamp"].to_list() == [utc(2024, 1, 31, 23, 58), utc(2024, 1, 31, 23, 59), utc(2024, 2, 1, 0, 0)]
    f = read_symbol(str(silver.SILVER_ROOT / "binance_um_funding"), "BTCUSDT").sort("timestamp")
    assert f["timestamp"].to_list() == [utc(2024, 1, 31), utc(2024, 1, 31, 8), utc(2024, 1, 31, 16)]
    assert set(f.columns) == set(FUNDING_SCHEMA)
