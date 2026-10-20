"""SEC 13F-HR of the superinvestors -> bronze/sec_13f_holdings -> gold/superinvestor_moves + _funds.

    1. for each fund in symbols.SUPERINVESTORS the last 3 original 13F-HR
       (EDGAR submissions); filings already stored are skipped
    2. their information tables, one row per position (bronze, keyed by accession)
    3. gold rebuilt for the latest quarter filed by most funds
    4. CUSIP -> ticker through OpenFIGI (cached, reference/cusip_ticker.parquet),
       only for what the desk shows: moves of 2+ funds or >= 0.5% of a book

First run ~3 minutes (about 150 filings + a few thousand CUSIPs to map),
then seconds until a fund files a new quarter. Needs SEC_USER_AGENT in .env.

Run:
    .venv/bin/python applications/historical/superinvestors.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable, write_deltalake

import quantlake.gold.superinvestors as gold
from quantlake.bronze.connectors.sec_13f import filings, info_table
from quantlake.bronze.connectors.sec_form4 import SECClient
from quantlake.config import BRONZE_ROOT
from quantlake.reference import cusip
from symbols import SUPERINVESTORS

PATH = str(BRONZE_ROOT / "sec_13f_holdings")
N_FILINGS = 3


def stored_accessions() -> set[str]:
    if not DeltaTable.is_deltatable(PATH):
        return set()
    return set(pl.from_arrow(DeltaTable(PATH).to_pyarrow_table(columns=["accession"]))["accession"].unique().to_list())


def main() -> None:
    sec = SECClient()
    have = stored_accessions()
    added = 0
    for name, cik in SUPERINVESTORS:
        try:
            fs = filings(sec, cik, N_FILINGS)
        except Exception as exc:
            print(f"  ! {name}: {exc}")
            continue
        for f in fs:
            if f["accession"] in have:
                continue
            rows = info_table(sec, f)
            if not rows:
                print(f"  ! {name} {f['period']}: no information table")
                continue
            df = pl.DataFrame(rows, infer_schema_length=None).with_columns(
                pl.lit(cik).alias("cik"), pl.lit(f["fund_name"]).alias("fund_name"),
                pl.lit(f["accession"]).alias("accession"), pl.lit(f["filed_date"]).alias("filed_date"),
                pl.lit(f["period"]).alias("period"), pl.lit(f["period"].year).cast(pl.Int32).alias("year"),
                pl.lit(datetime.now(timezone.utc)).cast(pl.Datetime("us", "UTC")).alias("ingested_at"),
            )
            mode = "append" if DeltaTable.is_deltatable(PATH) else "overwrite"
            write_deltalake(PATH, df.to_arrow(), mode=mode, partition_by=["year"], schema_mode="merge")
            have.add(f["accession"])
            added += 1
            print(f"[{name}] {f['period']} filed {f['filed_date']}: {len(rows)} positions")
    print(f"[13F] {added} new filings")

    holdings = pl.from_arrow(DeltaTable(PATH).to_pyarrow_table())
    moves, funds, quarter = gold.build(holdings, SUPERINVESTORS, cusip.load())
    # tickers only where the desk shows them: moves of 2+ funds, or >= 0.5% of a book
    acting = moves.filter(pl.col("action") != "HOLD")
    shared = acting.group_by("cusip").agg(pl.col("cik").n_unique().alias("n")).filter(pl.col("n") >= 2)["cusip"]
    big = acting.filter(pl.col("delta_w").abs() >= 0.005)["cusip"]
    need = sorted(set(shared.to_list()) | set(big.to_list()))
    tickers = cusip.resolve(need)
    print(f"[cusip] {tickers['ticker'].is_not_null().sum()}/{len(need)} mapped to a ticker")
    moves = moves.drop("ticker").join(cusip.load().select("cusip", "ticker"), on="cusip", how="left")
    gold.save(moves, funds)
    if moves.is_empty():
        print("[13F] no moves")
        return
    n_in = funds.filter("in_quarter").height
    acts = moves["action"].value_counts().sort("action").rows()
    print(f"[13F] quarter {quarter}: {n_in}/{funds.height} funds, moves {acts}")


if __name__ == "__main__":
    main()
