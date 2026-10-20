"""Insider activity -> gold/insider_activity/1d (current snapshot, rebuilt each run).

From bronze/sec_form4 (one row per Form 4 transaction) and nasdaq_stock_daily:
open-market purchases (code P) and sales (S) filed in the last WINDOW_DAYS days.

  buy        P with value >= MIN_BUY. The research signal: insiders sell for
             many reasons (taxes, diversification, 10b5-1 plans), they buy for one.
  sell       S with value >= MIN_SELL, flagged when under a 10b5-1 plan.
  cluster    per symbol, distinct insiders buying in the last CLUSTER_DAYS
             days (by trade date): two or more is the strongest pattern.

since_price = last close / price paid - 1, for the buys (prices from Nasdaq).
"""
from datetime import date, timedelta

import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

TABLE = "insider_activity"
TIMEFRAME = "1d"
WINDOW_DAYS = 30
CLUSTER_DAYS = 14
MIN_BUY = 10_000
MIN_SELL = 1_000_000


def role(df: pl.DataFrame) -> pl.Expr:
    return (
        pl.when(pl.col("officer_title").is_not_null()).then(pl.col("officer_title"))
        .when(pl.col("is_officer")).then(pl.lit("Officer"))
        .when(pl.col("is_director")).then(pl.lit("Director"))
        .when(pl.col("is_ten_pct")).then(pl.lit("10% owner"))
        .otherwise(pl.lit("Other")).alias("role")
    )


def build(form4: pl.DataFrame, prices: pl.DataFrame, today: date) -> pl.DataFrame:
    if form4.is_empty():
        return pl.DataFrame()
    start = today - timedelta(days=WINDOW_DAYS)
    tx = form4.filter(
        (pl.col("filed_date") >= start) & pl.col("symbol").is_not_null()
        & pl.col("code").is_in(["P", "S"]) & (pl.col("value") > 0)
    ).with_columns(
        pl.col("transaction_date").str.to_date("%Y-%m-%d", strict=False).alias("trade_date"),
        role(form4),
    ).with_columns(
        (pl.col("filed_date") - pl.col("trade_date")).dt.total_days().alias("delay_days"),
        pl.when(pl.col("code") == "P").then(pl.lit("buy")).otherwise(pl.lit("sell")).alias("list"),
    )
    # one row per insider, trade day, symbol and side: Form 4 splits a day into many fills
    tx = tx.group_by(["list", "symbol", "owner_cik", "trade_date"]).agg(
        pl.col("issuer_name").first(), pl.col("owner_name").first(), pl.col("role").first(),
        pl.col("is_director").first(), pl.col("is_officer").first(), pl.col("is_ten_pct").first(),
        pl.col("plan_10b5_1").any(), pl.col("direct").all(),
        pl.col("shares").sum(), pl.col("value").sum(), pl.col("shares_after").last(),
        pl.col("filed_date").max(), pl.col("delay_days").max(), pl.col("accession").first(),
        pl.col("n_owners").max(),
    ).with_columns((pl.col("value") / pl.col("shares")).alias("price"))
    tx = tx.filter(
        ((pl.col("list") == "buy") & (pl.col("value") >= MIN_BUY))
        | ((pl.col("list") == "sell") & (pl.col("value") >= MIN_SELL))
    )

    recent = tx.filter((pl.col("list") == "buy") & (pl.col("trade_date") >= today - timedelta(days=CLUSTER_DAYS)))
    cluster = recent.group_by("symbol").agg(
        pl.col("owner_cik").n_unique().alias("cluster_buyers"),
        pl.col("value").sum().alias("cluster_value"),
    )
    tx = tx.join(cluster, on="symbol", how="left").with_columns(
        pl.col("cluster_buyers").fill_null(0), pl.col("cluster_value").fill_null(0.0))

    if not prices.is_empty():
        last = prices.sort("timestamp").group_by("symbol").agg(
            pl.col("close").last().alias("last_close"),
            pl.col("timestamp").last().dt.convert_time_zone("America/New_York").dt.date().alias("last_close_date"))
        tx = tx.join(last, on="symbol", how="left").with_columns(
            pl.when(pl.col("list") == "buy").then(pl.col("last_close") / pl.col("price") - 1).alias("since_price"))
    else:
        tx = tx.with_columns(pl.lit(None, pl.Float64).alias("last_close"), pl.lit(None, pl.Date).alias("last_close_date"),
                             pl.lit(None, pl.Float64).alias("since_price"))
    return tx.with_columns(pl.lit(today).alias("as_of")).sort(
        ["list", "trade_date", "value"], descending=[False, True, True])


def save(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    write_deltalake(str(GOLD_ROOT / TABLE / TIMEFRAME), df.to_arrow(), mode="overwrite", schema_mode="overwrite")
