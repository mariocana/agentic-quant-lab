"""ES / NQ single contracts -> roll calendar -> continuous gold -> check vs @ES.

Reads one ExportBars CSV per contract from data/multicharts/, named with
the TradeStation code: ESZ25_1min.csv, NQH26_1min.csv (same format as the
@ES export). Partial history is fine, e.g. only the weeks around each roll.

  1. bronze/multicharts_contracts + silver (symbol = contract code); every
     CSV is re-read whole and overwrites its rows (files are small).
  2. reference/rolls: every quarterly roll between the first and last
     contract on file, gap_points measured where both contracts traded
     before roll_ts (null otherwise).
  3. gold/multicharts_continuous/<tf>: unadjusted bars + contract + adj_offset.
  4. Check against @ES / @NQ (silver/multicharts_ohlcv): sessions where
     TradeStation follows another contract, and its roll date vs ours.

Run:
    .venv/bin/python applications/historical/multicharts_rolls.py
    .venv/bin/python applications/historical/multicharts_rolls.py --check-only   # step 4 only
"""
import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
import quantlake.silver.ingest as silver
from quantlake.bronze.connectors.multicharts import MC_DIR, MultiChartsCSVConnector
from quantlake.config import SILVER_ROOT
from quantlake.gold.continuous import compare_with_reference, continuous_1m, roll_differences, write_continuous
from quantlake.reference.rolls import measure_gaps, read_rolls, roll_calendar, write_rolls
from quantlake.storage import read_symbol, symbols

ROOTS = ("ES", "NQ")
CHART_TZ = "America/Chicago"   # same chart settings as the @ES / @NQ exports
TABLE = "multicharts_contracts"
REFERENCE_TABLE = MultiChartsCSVConnector.TABLE_NAME   # @ES / @NQ, back-adjusted by TradeStation
FILE = re.compile(r"^((?:" + "|".join(ROOTS) + r")[HMUZ]\d{2})_1min\.csv$")


def contract_files(folder: Path = MC_DIR) -> dict[str, Path]:
    return {m.group(1): p for p in sorted(folder.glob("*_1min.csv")) if (m := FILE.match(p.name))}


def ingest_contracts(folder: Path = MC_DIR) -> list[str]:
    connector = MultiChartsCSVConnector(chart_tz=CHART_TZ, folder=folder)
    files = contract_files(folder)
    for code, path in files.items():
        df = connector.fetch(symbol=path.stem)
        if df.is_empty():
            print(f"[{code}] empty file")
            continue
        df = bronze.add_partition_columns(df, symbol=code)
        bronze.save(df, TABLE, update_matched=True)
        silver.ingest(df, TABLE, align_1m=True, update_matched=True)
        print(f"[{code}] {len(df):,} bars {df['timestamp'].min():%Y-%m-%d} → {df['timestamp'].max():%Y-%m-%d}")
    return sorted(files)


def load_contract_bars() -> pl.DataFrame:
    path = str(SILVER_ROOT / TABLE)
    frames = [read_symbol(path, code) for code in symbols(path)]
    frames = [f for f in frames if f is not None and not f.is_empty()]
    return pl.concat(frames, how="diagonal_relaxed").sort("symbol", "timestamp") if frames else pl.DataFrame()


def build(bars: pl.DataFrame) -> pl.DataFrame:
    rolls = measure_gaps(roll_calendar(bars["symbol"].unique().to_list()), bars)
    write_rolls(rolls)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=160):
        print(rolls)
    for root in ROOTS:
        series = continuous_1m(root, bars, rolls)
        if series.is_empty():
            continue
        written = write_continuous(series)
        print(f"[{root}] gold/multicharts_continuous: " + ", ".join(f"{tf} {n:,}" for tf, n in written.items()))
    return rolls


def check(bars: pl.DataFrame, rolls: pl.DataFrame) -> None:
    for root in ROOTS:
        ref = read_symbol(str(SILVER_ROOT / REFERENCE_TABLE), root)
        if ref is None or ref.is_empty():
            continue
        cmp = compare_with_reference(bars, ref, root, rolls)
        if cmp.is_empty():
            print(f"[{root}] no session with both @{root} and contracts")
            continue
        differ = cmp.filter(pl.col("theirs").is_not_null() & (pl.col("theirs") != pl.col("ours")))
        unmatched = cmp.filter(pl.col("theirs").is_null())
        print(f"[{root}] {cmp.height} sessions compared: {cmp.height - differ.height - unmatched.height} same contract, "
              f"{differ.height} on another contract, {unmatched.height} with no contract matching @{root}")
        with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=160):
            if not differ.is_empty():
                print(differ)
            print(roll_differences(cmp, rolls, root).filter(pl.col("ts_roll").is_not_null()))


def main() -> None:
    if "--check-only" not in sys.argv:
        files = ingest_contracts()
        if not files:
            print(f"no contract CSV (e.g. ESZ25_1min.csv) in {MC_DIR}")
            return
    bars = load_contract_bars()
    if bars.is_empty():
        print("no contract bars in silver")
        return
    rolls = read_rolls() if "--check-only" in sys.argv else build(bars)
    check(bars, rolls)


if __name__ == "__main__":
    main()
