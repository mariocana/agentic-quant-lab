"""Seed reference/instruments and print it.

Writes the default rows (ES, NQ, BTCUSDT, ETHUSDT, BTCUSDT-PERP) into
DATA_ROOT/reference/instruments. Safe to re-run: rows merge on symbol.

With --check-binance it also compares tick_size / qty_step / min_qty of
the crypto rows with Binance's live exchangeInfo (spot and USDⓈ-M), so you
notice when Binance changes a filter.

Run:
    poetry run python examples/reference/seed_instruments.py
    poetry run python examples/reference/seed_instruments.py --check-binance
"""
import sys

import httpx
import polars as pl

from quantlake.reference.instruments import read_instruments, seed_default, table_path

EXCHANGE_INFO = {
    "crypto_spot": "https://api.binance.com/api/v3/exchangeInfo",
    "crypto_perp": "https://fapi.binance.com/fapi/v1/exchangeInfo",  # USDⓈ-M, all symbols
}


def _live_filters(url: str) -> dict[str, dict[str, float]]:
    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    live = {}
    for s in resp.json()["symbols"]:
        f = {x["filterType"]: x for x in s["filters"]}
        live[s["symbol"]] = {
            "tick_size": float(f["PRICE_FILTER"]["tickSize"]),
            "qty_step":  float(f["LOT_SIZE"]["stepSize"]),
            "min_qty":   float(f["LOT_SIZE"]["minQty"]),
        }
    return live


def check_binance(df: pl.DataFrame) -> bool:
    ok = True
    for asset_class, url in EXCHANGE_INFO.items():
        rows = df.filter((pl.col("exchange") == "BINANCE") & (pl.col("asset_class") == asset_class))
        if rows.is_empty():
            continue
        live = _live_filters(url)
        for row in rows.iter_rows(named=True):
            specs = live.get(row["data_symbol"])
            if specs is None:
                ok = False
                print(f"MISSING {row['symbol']}: {row['data_symbol']} not in {url}")
                continue
            for field, value in specs.items():
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
