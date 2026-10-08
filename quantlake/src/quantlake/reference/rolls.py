"""reference/rolls: roll calendar of the continuous futures (ES, NQ).

One row per roll event; read by alpha-quant, so SCHEMA is a contract.

    symbol         root ("ES", "NQ")
    roll_ts        UTC instant the continuous series switches contract
    from_contract  TradeStation code of the expiring contract ("ESZ25")
    to_contract    next quarterly contract ("ESH26")
    gap_points     to_contract close - from_contract close at the last minute
                   both traded before roll_ts; null when the data to measure
                   it is missing

Roll rule (fixed calendar, known in advance, no look-ahead): CME equity
index futures expire on the third Friday of the contract month. The roll
day is the trading day 8 days earlier, the Thursday of the week before
(CME's roll date, when volume and open interest move to the next
quarter). With ROLL_AT_SESSION_OPEN the series switches at the open of the
roll day's Globex session, Wednesday 17:00 America/Chicago: the whole roll
day is already on the new contract, the side where the volume is that day.
Switching on a session boundary also means a 1h / 4h_cme / 1d_cme bar never
mixes two contracts. ROLL_AT_SESSION_OPEN = False switches at the end of
the roll day instead (Thursday 17:00 CT). Kept unless the check against
TradeStation's @ES shows its roll happens elsewhere.

Contract codes are TradeStation's: root + month code + two-digit year,
e.g. ESZ25 = December 2025, NQH26 = March 2026.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl
from deltalake import DeltaTable, write_deltalake

from quantlake.config import REFERENCE_ROOT

TABLE_NAME = "rolls"
CHICAGO = ZoneInfo("America/Chicago")
SESSION_OPEN = time(17, 0)          # Globex day session opens 17:00 CT the previous calendar day
ROLL_DAYS_BEFORE_EXPIRY = 8        # roll day = expiry (third Friday) - 8 days = Thursday
ROLL_AT_SESSION_OPEN = True        # switch at the open of the roll day's session (Wed 17:00 CT)
MONTH_CODES = "FGHJKMNQUVXZ"
QUARTERLY = "HMUZ"
GAP_LOOKBACK = timedelta(days=3)  # how far before roll_ts a common minute may be

SCHEMA: dict[str, pl.DataType] = {
    "symbol":        pl.String(),
    "roll_ts":       pl.Datetime("us", "UTC"),
    "from_contract": pl.String(),
    "to_contract":   pl.String(),
    "gap_points":    pl.Float64(),
}

_CODE = re.compile(r"^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$")


@dataclass(frozen=True, order=True)
class Contract:
    year: int
    month: int
    root: str

    @property
    def code(self) -> str:
        return f"{self.root}{MONTH_CODES[self.month - 1]}{self.year % 100:02d}"

    @property
    def expiry(self) -> date:
        """Third Friday of the contract month."""
        first = date(self.year, self.month, 1)
        first_friday = first + timedelta(days=(4 - first.weekday()) % 7)
        return first_friday + timedelta(weeks=2)

    @property
    def roll_day(self) -> date:
        """CME roll date: the trading day ROLL_DAYS_BEFORE_EXPIRY before expiry."""
        return self.expiry - timedelta(days=ROLL_DAYS_BEFORE_EXPIRY)

    @property
    def roll_ts(self) -> datetime:
        """When the continuous series leaves this contract (UTC): the open of the
        roll day's session (previous calendar day 17:00 CT) or, with
        ROLL_AT_SESSION_OPEN False, the end of it (roll day 17:00 CT)."""
        day = self.roll_day - timedelta(days=1) if ROLL_AT_SESSION_OPEN else self.roll_day
        return datetime.combine(day, SESSION_OPEN, tzinfo=CHICAGO).astimezone(timezone.utc)

    def next_quarterly(self) -> "Contract":
        months = [MONTH_CODES.index(m) + 1 for m in QUARTERLY]
        later = [m for m in months if m > self.month]
        return Contract(self.year, later[0], self.root) if later else Contract(self.year + 1, months[0], self.root)


def parse_contract(code: str) -> Contract:
    """'ESZ25' -> Contract(2025, 12, 'ES'). Two-digit years are 20YY."""
    m = _CODE.match(code)
    if m is None:
        raise ValueError(f"Not a TradeStation contract code: {code!r} (expected e.g. ESZ25)")
    root, month, yy = m.groups()
    return Contract(2000 + int(yy), MONTH_CODES.index(month) + 1, root)


def roll_calendar(contracts: list[str]) -> pl.DataFrame:
    """Every quarterly roll from the earliest to the latest contract given (gap_points null).

    Contracts missing in between still get their rolls, so a hole in the
    data shows up as rolls without gap_points instead of a silent jump.
    """
    parsed = sorted(parse_contract(c) for c in contracts)
    rows = []
    for root in sorted({c.root for c in parsed}):
        mine = [c for c in parsed if c.root == root]
        bad = [c.code for c in mine if MONTH_CODES[c.month - 1] not in QUARTERLY]
        if bad:
            raise ValueError(f"Only quarterly contracts (H, M, U, Z) roll in the continuous series: {bad}")
        current, last = mine[0], mine[-1]
        while current < last:
            nxt = current.next_quarterly()
            rows.append({"symbol": root, "roll_ts": current.roll_ts, "from_contract": current.code,
                         "to_contract": nxt.code, "gap_points": None})
            current = nxt
    return pl.DataFrame(rows, schema=SCHEMA).sort("symbol", "roll_ts")


def measure_gaps(calendar: pl.DataFrame, bars: pl.DataFrame) -> pl.DataFrame:
    """Fill gap_points from 1m contract bars (columns symbol = contract code, timestamp, close).

    gap = to close - from close at the last minute before roll_ts (within
    GAP_LOOKBACK) where both contracts have a non-NaN close.
    """
    gaps = []
    for row in calendar.iter_rows(named=True):
        window = bars.filter(
            pl.col("symbol").is_in([row["from_contract"], row["to_contract"]])
            & (pl.col("timestamp") < row["roll_ts"])
            & (pl.col("timestamp") >= row["roll_ts"] - GAP_LOOKBACK)
            & pl.col("close").is_not_nan()
        )
        wide = window.pivot(on="symbol", index="timestamp", values="close", aggregate_function="last")
        both = [row["from_contract"], row["to_contract"]]
        if not set(both) <= set(wide.columns):
            gaps.append(None)
            continue
        common = wide.drop_nulls(both).sort("timestamp")
        gaps.append(None if common.is_empty() else
                    common[-1, row["to_contract"]] - common[-1, row["from_contract"]])
    return calendar.with_columns(pl.Series("gap_points", gaps, dtype=pl.Float64))


def table_path() -> str:
    return str(REFERENCE_ROOT / TABLE_NAME)


def write_rolls(df: pl.DataFrame) -> None:
    """Replace the table (it is always rebuilt whole; old versions stay readable)."""
    if dict(df.schema) != SCHEMA:
        raise ValueError(f"reference/rolls schema {dict(df.schema)} != {SCHEMA}")
    if df.select(pl.struct("symbol", "roll_ts").is_duplicated().any()).item():
        raise ValueError("reference/rolls: duplicated (symbol, roll_ts)")
    write_deltalake(table_path(), df.sort("symbol", "roll_ts").to_arrow(), mode="overwrite")


def read_rolls(version: int | None = None) -> pl.DataFrame:
    path = table_path()
    if not DeltaTable.is_deltatable(path):
        raise FileNotFoundError(f"No Delta table at {path}: run applications/historical/multicharts_rolls.py")
    return pl.from_arrow(DeltaTable(path, version=version).to_pyarrow_table()).select(list(SCHEMA)).sort("symbol", "roll_ts")
