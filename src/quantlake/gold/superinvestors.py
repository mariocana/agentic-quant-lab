"""Superinvestor moves -> gold/superinvestor_moves/1q and gold/superinvestor_funds/1q.

From bronze/sec_13f_holdings (one row per 13F position) of the funds in
applications/symbols.SUPERINVESTORS.

  quarter   the latest period of report filed by at least MIN_SHARE of the
            funds still filing (13F are due 45 days after the quarter: early
            filers of the next quarter are not mixed in)
  moves     per fund holding that quarter and the previous one, per CUSIP:
            NEW / ADD / REDUCE / SOLD / HOLD, share change, portfolio weight
            before and after (long stock only: options and bonds left out)
  funds     every fund: latest period filed, whether it is in the quarter,
            positions and book value; stale = no filing for the quarter

flow_w = weight traded by the manager: for buys the new shares x price now /
book now, for sales the shares sold x price before / book before (SOLD: minus
the old weight), so it never exceeds the position's weight. Unlike delta_w = weight now - weight before,
it does not move with the price (a stock added while it fell keeps a positive
flow_w). The desk ranks stocks by how many funds bought (NEW + ADD) or sold
(REDUCE + SOLD), then by the summed flow_w.

Some filers still report values in thousands after the 2023 switch to
dollars: a filing whose median value per share is below $1 is scaled x1000.
"""
from datetime import date

import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

MIN_SHARE = 0.4
CHANGE_MIN = 0.01   # share change below 1% = HOLD


def _prev_quarter(d: date) -> date:
    m = (d.month - 1) // 3 * 3  # first month of the quarter, 0-based
    y, q_end_month = (d.year, m) if m else (d.year - 1, 12)
    return date(y, q_end_month, 31 if q_end_month in (3, 12) else 30)


def _book(h: pl.DataFrame) -> pl.DataFrame:
    """Long stock positions of one filing, one row per CUSIP, with weights."""
    s = h.filter(pl.col("put_call").is_null() & (pl.col("share_type") == "SH") & (pl.col("value_usd") > 0))
    per_share = (s["value_usd"] / s["shares"]).median() if s.height else None
    if per_share is not None and per_share < 1:   # reported in thousands
        s = s.with_columns(pl.col("value_usd") * 1000)
    s = s.group_by("cusip").agg(pl.col("issuer").first(), pl.col("title_class").first(),
                                pl.col("value_usd").sum(), pl.col("shares").sum())
    return s.with_columns((pl.col("value_usd") / pl.col("value_usd").sum()).alias("weight"))


def build(holdings: pl.DataFrame, managers: list[tuple[str, int]], tickers: pl.DataFrame
          ) -> tuple[pl.DataFrame, pl.DataFrame, date | None]:
    names = dict((cik, name) for name, cik in managers)
    h = holdings.filter(pl.col("cik").is_in(list(names)))
    if h.is_empty():
        return pl.DataFrame(), pl.DataFrame(), None
    latest = h.group_by("cik").agg(pl.col("period").max())
    per_period = latest.group_by("period").len().sort("period", descending=True)
    need = MIN_SHARE * latest.height
    quarter = None
    acc = 0
    for p, n in per_period.iter_rows():
        acc += n
        if acc >= need:   # funds whose latest filing is at or after p
            quarter = p
            break
    prev_q = _prev_quarter(quarter)

    moves, funds = [], []
    for cik, name in names.items():
        f = h.filter(pl.col("cik") == cik)
        last = f["period"].max() if not f.is_empty() else None
        cur, prev = f.filter(pl.col("period") == quarter), f.filter(pl.col("period") == prev_q)
        info = {"cik": cik, "manager": name, "latest_period": last, "in_quarter": not cur.is_empty(),
                "has_previous": not prev.is_empty(),
                "filed_date": cur["filed_date"].max() if not cur.is_empty() else None}
        if cur.is_empty():
            funds.append({**info, "positions": None, "book_value": None})
            continue
        b_cur = _book(cur)
        funds.append({**info, "positions": b_cur.height, "book_value": b_cur["value_usd"].sum()})
        if prev.is_empty():
            continue
        b_prev = _book(prev)
        m = b_cur.join(b_prev, on="cusip", how="full", coalesce=True, suffix="_prev").with_columns(
            pl.coalesce("issuer", "issuer_prev").alias("issuer"),
            pl.coalesce("title_class", "title_class_prev").alias("title_class"),
            pl.col("shares").fill_null(0.0), pl.col("shares_prev").fill_null(0.0),
            pl.col("weight").fill_null(0.0), pl.col("weight_prev").fill_null(0.0),
            pl.col("value_usd").fill_null(0.0),
        ).with_columns(
            pl.when(pl.col("shares_prev") == 0).then(pl.lit("NEW"))
            .when(pl.col("shares") == 0).then(pl.lit("SOLD"))
            .when(pl.col("shares") / pl.col("shares_prev") - 1 > CHANGE_MIN).then(pl.lit("ADD"))
            .when(pl.col("shares") / pl.col("shares_prev") - 1 < -CHANGE_MIN).then(pl.lit("REDUCE"))
            .otherwise(pl.lit("HOLD")).alias("action"),
            pl.when(pl.col("shares_prev") > 0).then(pl.col("shares") / pl.col("shares_prev") - 1).alias("shares_change"),
            (pl.col("weight") - pl.col("weight_prev")).alias("delta_w"),
            # bought: share of today's position that is new x today's weight (<= weight now)
            # sold: share of the old position that went x the old weight (>= - weight before)
            pl.when(pl.col("shares") == 0).then(-pl.col("weight_prev"))
            .when(pl.col("shares") >= pl.col("shares_prev"))
            .then((pl.col("shares") - pl.col("shares_prev")) / pl.col("shares") * pl.col("weight"))
            .otherwise((pl.col("shares") - pl.col("shares_prev")) / pl.col("shares_prev") * pl.col("weight_prev"))
            .alias("flow_w"),
        ).select("cusip", "issuer", "title_class", "action", "shares_prev", "shares", "shares_change",
                 "weight_prev", "weight", "delta_w", "flow_w", pl.col("value_usd").alias("value_now"))
        moves.append(m.with_columns(pl.lit(cik).alias("cik"), pl.lit(name).alias("manager")))

    mv = pl.concat(moves) if moves else pl.DataFrame()
    if not mv.is_empty():
        mv = mv.join(tickers.select("cusip", "ticker"), on="cusip", how="left").with_columns(
            pl.lit(quarter).alias("quarter"), pl.lit(prev_q).alias("previous_quarter"))
    fd = pl.DataFrame(funds, infer_schema_length=None).with_columns(pl.lit(quarter).alias("quarter"))
    return mv, fd, quarter


def save(moves: pl.DataFrame, funds: pl.DataFrame) -> None:
    if not moves.is_empty():
        write_deltalake(str(GOLD_ROOT / "superinvestor_moves" / "1q"), moves.to_arrow(), mode="overwrite",
                        schema_mode="overwrite")
    if not funds.is_empty():
        write_deltalake(str(GOLD_ROOT / "superinvestor_funds" / "1q"), funds.to_arrow(), mode="overwrite",
                        schema_mode="overwrite")
