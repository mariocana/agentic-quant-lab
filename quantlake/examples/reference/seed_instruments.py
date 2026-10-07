"""Seed reference/instruments and print it.

Writes the default rows (ES, NQ, BTCUSDT, ETHUSDT) into
DATA_ROOT/reference/instruments. Safe to re-run: rows merge on symbol.

With --check-binance it also compares tick_size / qty_step / min_qty of
the crypto rows with Binance's live exchangeInfo, so you notice when
Binance changes a filter.

Run:
    poetry run python examples/reference/seed_instruments.py
    poetry run python examples/reference/seed_instruments.py --check-binance
"""
import sys

import httpx
import polars as pl

from quantlake.reference.instruments import read_instruments, seed_default, table_path

EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"


def check_binance(df: pl.DataFrame) -> bool:
    rows = df.filter(pl.col("exchange") == "BINANCE")
    symbols = rows["data_symbol"].to_list()
    resp = httpx.get(EXCHANGE_INFO, params={"symbols": str(symbols).replace("'", '"').replace(" ", "")}, timeout=30)
    resp.raise_for_status()
    live = {}
    for s in resp.json()["symbols"]:
        f = {x["filterType"]: x for x in s["filters"]}
        live[s["symbol"]] = {
            "tick_size": float(f["PRICE_FILTER"]["tickSize"]),
            "qty_step":  float(f["LOT_SIZE"]["stepSize"]),
            "min_qty":   float(f["LOT_SIZE"]["minQty"]),
        }
    ok = True
    for row in rows.iter_rows(named=True):
        for field, value in live[row["data_symbol"]].items():
            if row[field] != value:
                ok = False
                print(f"MISMATCH {row['symbol']}.{field}: table {row[field]} vs Binance {value}")
    print("Binance specs match" if ok else "Update DEFAULT_INSTRUMENTS and re-run")
    return ok


seed_default()
df = read_instruments()

pl.Config.set_tbl_cols(-1)
pl.Config.set_tbl_width_chars(200)
print(f"{table_path()}  ({df.height} instruments)")
print(df.drop("updated_at", "description"))
print(df.schema)

if "--check-binance" in sys.argv and not check_binance(df):
    sys.exit(1)
