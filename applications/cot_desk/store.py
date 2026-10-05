"""Read-only data layer for the COT desk: gold/cot_positioning/1w.

Replaces cot-analyzer's db.py (Postgres). The whole table is a few tens
of thousands of rows, so it is loaded once into Polars and reloaded only
when the Delta table version changes (i.e. after a sync).

Rows already carry week-over-week changes and z26/z52 computed on prior
weeks only (see quantlake.gold.cot), so nothing is recomputed here.
"""
import threading
from datetime import date

import polars as pl
from deltalake import DeltaTable

import quantlake.gold.cot as gold_cot
from quantlake.config import GOLD_ROOT

GOLD_PATH = str(GOLD_ROOT / gold_cot.TABLE / gold_cot.TIMEFRAME)

_cache: dict = {"version": None, "df": None}
_lock = threading.Lock()


def _gold() -> pl.DataFrame:
    if not DeltaTable.is_deltatable(GOLD_PATH):
        return pl.DataFrame()
    dt = DeltaTable(GOLD_PATH)
    with _lock:
        if _cache["version"] != dt.version():
            _cache["df"] = pl.from_arrow(dt.to_pyarrow_table()).sort(["symbol", "report_date"])
            _cache["version"] = dt.version()
        return _cache["df"]


def latest_rows(as_of: date | None = None) -> dict[str, dict]:
    """Most recent row per symbol (report_date <= as_of when given)."""
    df = _gold()
    if df.is_empty():
        return {}
    if as_of is not None:
        df = df.filter(pl.col("report_date") <= as_of)
    last = df.group_by("symbol").agg(pl.all().sort_by("report_date").last())
    return {r["symbol"]: r for r in last.iter_rows(named=True)}


def history(symbol: str, as_of: date | None = None, limit_weeks: int | None = None) -> list[dict]:
    """Rows for one symbol, oldest first."""
    df = _gold()
    if df.is_empty():
        return []
    df = df.filter(pl.col("symbol") == symbol)
    if as_of is not None:
        df = df.filter(pl.col("report_date") <= as_of)
    if limit_weeks is not None:
        df = df.tail(limit_weeks)
    return df.to_dicts()


def available_report_dates() -> list[date]:
    """Distinct report dates, newest first (feeds the date dropdown)."""
    df = _gold()
    if df.is_empty():
        return []
    return df["report_date"].unique().sort(descending=True).to_list()


def newest_by_symbol() -> dict[str, date]:
    """Latest report_date per symbol."""
    df = _gold()
    if df.is_empty():
        return {}
    return dict(df.group_by("symbol").agg(pl.col("report_date").max()).iter_rows())


def row_count() -> int:
    return _gold().height


def symbol_count() -> int:
    df = _gold()
    return 0 if df.is_empty() else df["symbol"].n_unique()
