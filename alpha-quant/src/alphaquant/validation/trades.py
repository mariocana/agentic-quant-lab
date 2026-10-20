"""TradeLog: the one input every validation stage reads.

A trade list can come from a MultiCharts Performance Report (.xlsx), from the
Colab CSV written by mc/docs/to_colab_csv.py, or from an alpha-quant SimResult.
All three become the same frame, so Stages 2-7 never care where trades came from.

Columns:
    entry_time  naive datetime on the session's clock (MultiCharts exports
                exchange time; a SimResult is converted with `tz`)
    pnl         net P&L of the trade in account currency, costs already in
    mae         worst excursion inside the trade, <= 0 and never above pnl
                (MultiCharts "Drawdown ($)"; when unknown, min(0, pnl))
    contracts   size of the trade
    direction   +1 long, -1 short
"""
import csv
import html
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from alphaquant.engine import SimResult

TRADE_LOG_SCHEMA = pl.Schema({
    "entry_time": pl.Datetime("us"),
    "pnl": pl.Float64(),
    "mae": pl.Float64(),
    "contracts": pl.Float64(),
    "direction": pl.Int8(),
})

_EXCEL_EPOCH = datetime(1899, 12, 30)

Day = list[tuple[float, float]]  # (pnl, mae) of each trade, in order


@dataclass(frozen=True)
class TradeLog:
    frame: pl.DataFrame
    source: str = ""

    def __post_init__(self) -> None:
        if self.frame.schema != TRADE_LOG_SCHEMA:
            raise ValueError(f"TradeLog schema {dict(self.frame.schema)} != expected {dict(TRADE_LOG_SCHEMA)}")

    # ── constructors ──────────────────────────────────────────────────────

    @classmethod
    def from_rows(cls, rows: list[dict], source: str = "") -> "TradeLog":
        """Rows with entry_time and pnl; mae, contracts and direction are optional."""
        out = []
        for r in rows:
            pnl = float(r["pnl"])
            mae = r.get("mae")
            mae = min(0.0, pnl) if mae is None else min(0.0, float(mae), pnl)
            out.append({
                "entry_time": r["entry_time"],
                "pnl": pnl,
                "mae": mae,
                "contracts": float(r.get("contracts", 1.0)),
                "direction": int(r.get("direction", 1)),
            })
        frame = pl.DataFrame(out, schema=TRADE_LOG_SCHEMA).sort("entry_time", maintain_order=True)
        return cls(frame, source)

    @classmethod
    def from_pnl(cls, pnl: list[float], start: datetime = datetime(2020, 1, 2), source: str = "") -> "TradeLog":
        """One trade per calendar day from `start`. For tests and quick what-ifs."""
        return cls.from_rows(
            [{"entry_time": start + timedelta(days=i), "pnl": p} for i, p in enumerate(pnl)], source,
        )

    @classmethod
    def from_mc_xlsx(cls, path: str | Path) -> "TradeLog":
        """List of Trades of a MultiCharts Performance Report. The P&L sits on the entry row."""
        path = Path(path)
        with zipfile.ZipFile(path) as z:
            sheet = _find_sheet(z, "List of Trades")
            if sheet is None:
                raise ValueError(f"{path.name}: no 'List of Trades' sheet")
            rows = _sheet_rows(z, sheet)
        hdr = next((i for i, r in enumerate(rows[:10]) if any(c.strip() == "Profit ($)" for c in r)), None)
        if hdr is None:
            raise ValueError(f"{path.name}: column 'Profit ($)' not found")
        col = {c.strip(): j for j, c in enumerate(rows[hdr])}

        def cell(r: list[str], name: str) -> str:
            j = col.get(name)
            return r[j].strip() if j is not None and j < len(r) else ""

        out = []
        for r in rows[hdr + 1:]:
            pnl, when = _float(cell(r, "Profit ($)")), _excel_datetime(cell(r, "Date"))
            if pnl is None or when is None:
                continue                      # exit row, or a footer
            out.append({
                "entry_time": when,
                "pnl": pnl,
                "mae": _float(cell(r, "Drawdown ($)")),
                "contracts": _float(cell(r, "Contracts")) or 1.0,
                "direction": -1 if "SHORT" in cell(r, "Type").upper() else 1,
            })
        return cls.from_rows(out, path.name)

    @classmethod
    def from_colab_csv(cls, path: str | Path) -> "TradeLog":
        """CSV written by mc/docs/to_colab_csv.py (one row per trade)."""
        path = Path(path)
        out = []
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                r = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
                pnl, when = _float(r.get("profit_usd", "")), _excel_datetime(r.get("excel_date", ""))
                if pnl is None or when is None:
                    continue
                out.append({
                    "entry_time": when,
                    "pnl": pnl,
                    "mae": _float(r.get("drawdown_usd", "")),
                    "contracts": _float(r.get("contracts", "")) or 1.0,
                    "direction": -1 if r.get("direction", "").upper() == "SHORT" else 1,
                })
        return cls.from_rows(out, path.name)

    @classmethod
    def from_simresult(cls, result: SimResult, tz: str = "UTC", source: str = "") -> "TradeLog":
        """Trades of a simulation. `tz` is the clock that defines a trading day.

        TRADE_SCHEMA has no excursion inside the trade, so mae falls back to the
        closing loss: Stage 7 is then less conservative than on a MultiCharts list.
        """
        t = result.trades
        frame = pl.DataFrame({
            "entry_time": t["entry_time"].dt.convert_time_zone(tz).dt.replace_time_zone(None),
            "pnl": t["net_pnl_account"],
            "mae": t["net_pnl_account"].clip(upper_bound=0.0),
            "contracts": t["qty"],
            "direction": t["side"],
        }, schema=TRADE_LOG_SCHEMA).sort("entry_time", maintain_order=True)
        return cls(frame, source or str(result.meta.get("strategy", "")))

    # ── views ─────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return self.frame.height

    @property
    def pnl(self) -> np.ndarray:
        return self.frame["pnl"].to_numpy()

    @property
    def years(self) -> list[int]:
        return self.frame["entry_time"].dt.year().to_list()

    def between(self, start: date | None = None, end: date | None = None) -> "TradeLog":
        """Trades entered on dates in [start, end], both inclusive."""
        d = pl.col("entry_time").dt.date()
        cond = pl.lit(True)
        if start is not None:
            cond &= d >= start
        if end is not None:
            cond &= d <= end
        return TradeLog(self.frame.filter(cond), self.source)

    def halves(self) -> tuple["TradeLog", "TradeLog"]:
        """First and second half by trade count (Stage 4 split-sample)."""
        k = self.frame.height // 2
        return TradeLog(self.frame.head(k), self.source), TradeLog(self.frame.slice(k), self.source)

    def to_micro(self, ratio: float = 10.0, cost_in_report: float = 15.0, cost_micro: float = 1.50) -> "TradeLog":
        """Per-contract P&L of a full-size list, rescaled to 1 micro with the micro's real costs.

        `cost_in_report` is the round turn already inside pnl (NQ: $7.50 per side);
        it is added back, the gross is divided by `ratio`, and `cost_micro` is charged.
        The cost per micro is close to triple the mini's in proportion (pipeline_prop.md).
        """
        c = pl.col("contracts")
        micro = (pl.col("pnl") / c + cost_in_report) / ratio - cost_micro
        frame = self.frame.with_columns(
            pnl=micro,
            mae=pl.min_horizontal(pl.lit(0.0), pl.col("mae") / c / ratio, micro),
            contracts=pl.lit(1.0),
        )
        return TradeLog(frame, self.source)

    def days(self) -> list[tuple[date, Day]]:
        """Trades grouped by entry date, in order: the unit Stage 7 resamples."""
        out: list[tuple[date, Day]] = []
        for d, p, m in zip(self.frame["entry_time"].dt.date(), self.frame["pnl"], self.frame["mae"]):
            if not out or out[-1][0] != d:
                out.append((d, []))
            out[-1][1].append((p, m))
        return out


# ── MultiCharts xlsx, standard library only (same reader as mc/docs/check_report.py) ──

def _sheet_rows(z: zipfile.ZipFile, n: int) -> list[list[str]]:
    shared = []
    try:
        s = z.read("xl/sharedStrings.xml").decode("utf8", "replace")
        shared = [html.unescape(re.sub(r"<.*?>", "", m.group(1))) for m in re.finditer(r"<si>(.*?)</si>", s, re.S)]
    except KeyError:
        pass
    x = z.read(f"xl/worksheets/sheet{n}.xml").decode("utf8", "replace")
    rows = []
    for rm in re.finditer(r"<row[^>]*>(.*?)</row>", x, re.S):
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*)>(.*?)</c>', rm.group(1), re.S):
            ref, attr, body = cm.groups()
            vm = re.search(r"<v>(.*?)</v>", body, re.S)
            if vm is None:
                tm = re.search(r"<t[^>]*>(.*?)</t>", body, re.S)
                cells[ref] = html.unescape(tm.group(1)) if tm else ""
                continue
            v = vm.group(1)
            cells[ref] = html.unescape(shared[int(v)] if 't="s"' in attr else v)
        if cells:
            row = [""] * (max(map(_col_index, cells)) + 1)
            for ref, v in cells.items():
                row[_col_index(ref)] = v
            rows.append(row)
    return rows


def _col_index(ref: str) -> int:
    k = 0
    for ch in ref:
        k = k * 26 + ord(ch) - 64
    return k - 1


def _find_sheet(z: zipfile.ZipFile, title: str) -> int | None:
    """MultiCharts does not keep a fixed sheet order: match the title in A1."""
    for n in range(1, 13):
        try:
            rows = _sheet_rows(z, n)
        except KeyError:
            continue
        if rows and rows[0] and title.lower() in rows[0][0].lower():
            return n
    return None


def _float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _excel_datetime(v: str) -> datetime | None:
    serial = _float(v)
    if serial is None:
        return None
    # rounded to the second: Excel serials carry float noise
    return _EXCEL_EPOCH + timedelta(seconds=round(serial * 86400))
