"""Bronze ingest of the desk's market files. The data cannot be re-downloaded from
Hyperliquid, so the tests are about never losing or duplicating a row."""
import gzip
import json

import polars as pl
from deltalake import DeltaTable

from quantlake.bronze.connectors import hyperliquid_market as hm


def _sample(ts: str, oi: str = "1000") -> dict:
    return {"ts": ts, "errors": [], "dexs": [
        {"dex": "", "data": [
            {"universe": [{"name": "BTC", "szDecimals": 5, "maxLeverage": 40, "marginTableId": 56},
                          {"name": "UNI", "szDecimals": 1, "maxLeverage": 10, "isDelisted": True}]},
            [{"markPx": "100.5", "midPx": "100.4", "oraclePx": "100.6", "funding": "0.0000125",
              "openInterest": oi, "dayNtlVlm": "5e6", "premium": None, "impactPxs": ["100.3", "100.6"]},
             {"markPx": "5.1", "midPx": None, "funding": "0", "openInterest": "0", "impactPxs": None}]]},
        {"dex": "xyz", "data": [
            {"universe": [{"name": "xyz:TSLA", "szDecimals": 3, "maxLeverage": 10, "onlyIsolated": True}]},
            [{"markPx": "250", "midPx": "250.1", "funding": "0.00001", "openInterest": "42"}]]},
    ]}


def _day(*samples) -> bytes:
    return b"".join(gzip.compress((json.dumps(s) + "\n").encode()) for s in samples)


def test_one_row_per_dex_and_asset_with_delisted_kept():
    df = hm.parse_sample(_sample("2026-11-09T10:00:00+00:00"))
    assert df.height == 3
    assert set(zip(df["dex"], df["asset"])) == {("main", "BTC"), ("main", "UNI"), ("xyz", "xyz:TSLA")}
    uni = df.filter(pl.col("asset") == "UNI").row(0, named=True)
    assert uni["is_delisted"] is True and uni["mid_px"] is None      # delisted: no book, still a row
    btc = df.filter(pl.col("asset") == "BTC").row(0, named=True)
    assert btc["mark_px"] == 100.5 and btc["open_interest"] == 1000.0 and btc["premium"] is None
    assert (btc["impact_bid_px"], btc["impact_ask_px"]) == (100.3, 100.6)
    assert df.filter(pl.col("asset") == "xyz:TSLA")["only_isolated"].item() is True


def test_a_truncated_last_sample_is_dropped_not_fatal():
    whole = _day(_sample("2026-11-09T10:00:00+00:00"), _sample("2026-11-09T11:00:00+00:00"))
    third = gzip.compress(json.dumps(_sample("2026-11-09T12:00:00+00:00")).encode())
    assert len(hm.read_samples(whole + third[: len(third) // 2])) == 2


class FakeDesk:
    def __init__(self, files: dict[str, bytes]):
        self.files, self.downloads = files, []

    def days(self):
        return [{"day": d, "bytes": len(b)} for d, b in sorted(self.files.items())]

    def download(self, day):
        self.downloads.append(day)
        return self.files[day]


def test_pull_fetches_only_new_or_grown_days(tmp_path):
    desk = FakeDesk({"2026-11-08": _day(_sample("2026-11-08T23:00:00+00:00")),
                     "2026-11-09": _day(_sample("2026-11-09T00:00:00+00:00"))})
    assert len(hm.pull(desk, tmp_path)) == 2

    desk.downloads.clear()
    assert hm.pull(desk, tmp_path) == [] and desk.downloads == []          # nothing changed

    desk.files["2026-11-09"] += _day(_sample("2026-11-09T01:00:00+00:00"))   # today grew
    assert [p.name for p in hm.pull(desk, tmp_path)] == ["2026-11-09.jsonl.gz"]
    assert desk.downloads == ["2026-11-09"]


def test_ingest_is_idempotent_and_takes_the_grown_day(tmp_path):
    table = str(tmp_path / "table")
    raw = tmp_path / "raw"
    raw.mkdir()
    day = raw / "2026-11-09.jsonl.gz"
    day.write_bytes(_day(_sample("2026-11-09T00:00:00+00:00")))

    assert hm.ingest([day], table) == 3
    hm.ingest([day], table)                                              # same file again
    assert DeltaTable(table).to_pyarrow_table().num_rows == 3, "re-ingest duplicated rows"

    day.write_bytes(day.read_bytes() + _day(_sample("2026-11-09T01:00:00+00:00", oi="1200")))
    hm.ingest([day], table)
    df = pl.from_arrow(DeltaTable(table).to_pyarrow_table())
    assert df.height == 6
    oi = df.filter(pl.col("asset") == "BTC").sort("timestamp")["open_interest"].to_list()
    assert oi == [1000.0, 1200.0]


def test_partitioned_by_dex_not_by_asset(tmp_path):
    """~560 assets hourly would mean one tiny file per asset per run."""
    raw = tmp_path / "2026-11-09.jsonl.gz"
    raw.write_bytes(_day(_sample("2026-11-09T00:00:00+00:00")))
    hm.ingest([raw], str(tmp_path / "t"))
    assert DeltaTable(str(tmp_path / "t")).metadata().partition_columns == ["dex", "year", "month"]
