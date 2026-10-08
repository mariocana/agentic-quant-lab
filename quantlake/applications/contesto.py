"""Contesto automatico per la scheda di sessione (playbook Stucchi).

    contesto.py london   -> blocco per la scheda di Londra (prima delle 09:00)
    contesto.py ny       -> blocco per la scheda di NY (parte A, prima delle 15:30)

Prima aggiorna i dati (foto della catena scattate dal job Railway su R2,
VIX/GEX/NDX, barre MultiCharts, gold/daily_context; per NY anche una foto della
catena SPX adesso, per l'EM 0DTE), poi stampa in markdown un
blocco che sessioni/nuova_sessione.sh inserisce in cima alla scheda.
--no-update salta l'aggiornamento. I log dei loader vanno in data/logs/contesto.log.

Le probabilità (range di Londra, chiusura del gap, trend day con GEX basso) sono
ricalcolate a ogni lancio su tutto lo storico di gold/daily_context: vedi
education/enrico_stucchi/CALIBRAZIONE_contesto.md.
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
from deltalake import DeltaTable

from quantlake.config import DATA_ROOT, GOLD_ROOT, SILVER_ROOT
from quantlake.storage import read_symbol

APP = Path(__file__).resolve().parent
PY = sys.executable
ROME = ZoneInfo("Europe/Rome")
LOG = DATA_ROOT / "logs" / "contesto.log"
STALE = timedelta(minutes=30)   # barre più vecchie di così = CSV MultiCharts non aggiornato
IT = {"low": "bassa", "high": "alta", "up": "su", "down": "giù", "positive": "positivo", "negative": "negativo"}
EM_STUCCHI = "±1 EM toccato nel ~75% delle sessioni, oltre ±2 EM nel ~21%, chiusura entro ±2 EM nell'~89-91%"

LOADERS = {
    "london": ["cloud_sync.py", "historical/cboe_vix.py", "historical/squeezemetrics.py", "historical/nasdaq_index.py",
               "historical/multicharts.py", "historical/daily_context.py"],
    "ny": ["cloud_sync.py", "historical/multicharts.py", "historical/daily_context.py", "spx_chain_snapshot.py"],
}


def n(x, d=1, pct=False) -> str:
    """Numero all'italiana: 7.851,25 / 0,35 / 12%."""
    if x is None:
        return "–"
    if pct:
        return f"{x * 100:.0f}%"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def update(session: str) -> list[str]:
    warn = []
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as log:
        log.write(f"=== {datetime.now():%F %T} contesto {session}\n")
        log.flush()
        for script in LOADERS[session]:
            r = subprocess.run([PY, str(APP / script)], cwd=APP.parent, stdout=log, stderr=log)
            if r.returncode != 0:
                warn.append(f"aggiornamento fallito: {script} (vedi data/logs/contesto.log)")
    return warn


def context() -> pl.DataFrame:
    return pl.from_arrow(DeltaTable(str(GOLD_ROOT / "daily_context" / "1d")).to_pyarrow_table()).sort("symbol", "date")


def last_bar(symbol: str) -> tuple[datetime | None, float | None]:
    since = datetime.now(timezone.utc) - timedelta(days=5)
    b = read_symbol(str(SILVER_ROOT / "multicharts_ohlcv"), symbol, columns=["timestamp", "close"], since=since)
    if b is None or b.is_empty():
        return None, None
    r = b.sort("timestamp").row(-1, named=True)
    return r["timestamp"] + timedelta(minutes=1), r["close"]


def em_0dte() -> dict | None:
    path = GOLD_ROOT / "em_0dte" / "snapshot"
    if not DeltaTable.is_deltatable(str(path)):
        return None
    e = pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table()).sort("timestamp")
    today = datetime.now(ZoneInfo("America/New_York")).date()
    e = e.filter(pl.col("expiry") == today)
    return None if e.is_empty() else e.row(-1, named=True)


def it(x: str | None) -> str:
    return "–" if x is None else IT.get(x, x)


def rome(ts: datetime | None) -> str:
    return "–" if ts is None else ts.astimezone(ROME).strftime("%d/%m %H:%M")


def history(ctx: pl.DataFrame) -> pl.DataFrame:
    return ctx.filter("complete")


def london_quantiles(h: pl.DataFrame, symbol: str) -> tuple[float, float, float]:
    x = h.filter((pl.col("symbol") == symbol) & pl.col("london_range_em").is_not_null())["london_range_em"]
    return x.quantile(0.25), x.quantile(0.5), x.quantile(0.75)


def gap_fill_rate(h: pl.DataFrame, symbol: str, gap_em: float) -> tuple[float, int, str]:
    edges = [0, 0.1, 0.25, 0.5, 1.0, 99]
    a = abs(gap_em)
    lo, hi = next((lo, hi) for lo, hi in zip(edges, edges[1:]) if a < hi)
    x = h.filter((pl.col("symbol") == symbol) & pl.col("gap_filled").is_not_null()
                 & (pl.col("gap_em").abs() >= lo) & (pl.col("gap_em").abs() < hi))
    label = f"{n(lo, 2)}–{n(hi, 2)} EM" if hi < 99 else f"> {n(lo, 2)} EM"
    return (x["gap_filled"].mean() if x.height else None), x.height, label


def trend_rate(h: pl.DataFrame, symbol: str, low: bool) -> float:
    x = h.filter((pl.col("symbol") == symbol) & pl.col("gex_pct").is_not_null())
    x = x.filter(pl.col("gex_pct") < 0.3) if low else x.filter(pl.col("gex_pct") >= 0.3)
    return (x["day_type"] != "rotation").mean()


def header(warn: list[str], today: dict) -> list[str]:
    now = datetime.now(ROME)
    out = [f"## 0. Contesto automatico (quantlake, {now:%H:%M})", ""]
    bars = []
    for sym in ("ES", "NQ"):
        ts, _ = last_bar(sym)
        bars.append(f"{sym} fino alle {rome(ts)}")
        if ts is None or now - ts > STALE:
            warn.append(f"barre {sym} ferme alle {rome(ts)}: il CSV di MultiCharts non è aggiornato, "
                        "range asiatico e prezzo ora non sono affidabili")
    r = today["ES"]
    out.append(f"Dati: barre {', '.join(bars)} · VIX/GEX della chiusura precedente · sessione del {r['date']:%d/%m}")
    out += [f"> ⚠ {w}" for w in warn]
    return out + [""]


def london(ctx: pl.DataFrame, warn: list[str]) -> str:
    today = {s: ctx.filter(pl.col("symbol") == s).row(-1, named=True) for s in ("ES", "NQ")}
    h = history(ctx)
    out = header(warn, today)
    rows = {"Ieri RTH H / L / C": [], "EM giornaliero (VIX per ES, VXN per NQ)": [],
            "Range Londra atteso p25 / p50 / p75": [], "Asia H / L (range)": [], "Prezzo ora": [],
            "Mercato fermo se lo stop supera": []}
    for s in ("ES", "NQ"):
        r = today[s]
        q25, q50, q75 = london_quantiles(h, s)
        em = r["em"]
        _, px = last_bar(s)
        rows["Ieri RTH H / L / C"].append(f"{n(r['prev_high'], 2)} / {n(r['prev_low'], 2)} / {n(r['prev_close'], 2)}")
        rows["EM giornaliero (VIX per ES, VXN per NQ)"].append(f"**{n(em, 0)} pt** (IV {n(r['iv'])}, {n(r['iv_pct'], pct=True)} dell'anno)")
        rows["Range Londra atteso p25 / p50 / p75"].append(" / ".join(n(q * em, 0) if em else "–" for q in (q25, q50, q75)) + " pt")
        rows["Asia H / L (range)"].append(f"{n(r['asia_high'], 2)} / {n(r['asia_low'], 2)} ({n(r['asia_range'], 2)})")
        rows["Prezzo ora"].append(n(px, 2))
        rows["Mercato fermo se lo stop supera"].append(f"**{n(q25 * em / 2, 1)} pt**" if em else "–")
    out += ["| | ES | NQ |", "|---|---|---|"] + [f"| {k} | {v[0]} | {v[1]} |" for k, v in rows.items()]

    r = today["ES"]
    low = r["gex_pct"] is not None and r["gex_pct"] < 0.3
    out += [
        "",
        f"- **Volatilità** {it(r['vol_regime'])} ({n(r['iv_pct'], pct=True)} dell'anno), trend 20 giorni "
        f"{it(r['trend20'])} → quadrante `{r['quadrant'] or '–'}`. Term structure VIX9D/VIX {n(r['term_9d'], 2)}"
        f"{' → **stress a breve**' if (r['term_9d'] or 0) > 1 else ''}.",
        f"- **GEX** {it(r['gex_regime'])}, {n(r['gex_pct'], pct=True)} dell'anno"
        + (f" → **GEX basso: trend day {n(trend_rate(h, 'ES', True), pct=True)} contro "
           f"{n(trend_rate(h, 'ES', False), pct=True)}. Interruttore trend day (§2.0) con un solo segnale.**"
           if low else " → regime normale per i fade."),
        "- **Mercato fermo** (§1.3): in un quarto delle mattine Londra fa meno del p25. Se il tuo stop è più "
        "grande del valore in tabella, l'oscillazione attesa non arriva a 2× lo stop: si guarda e basta.",
        "- Il regime della mattina (rotazionale o direzionale) non si prevede da questi numeri: si legge live "
        "dall'accettazione (§1.3).",
    ]
    return "\n".join(out)


def ny(ctx: pl.DataFrame, warn: list[str]) -> str:
    today = {s: ctx.filter(pl.col("symbol") == s).row(-1, named=True) for s in ("ES", "NQ")}
    h = history(ctx)
    out = header(warn, today)
    e = em_0dte()
    if e is None:
        warn_line = "> ⚠ nessuna foto 0DTE di oggi nella catena SPX: EM live non disponibile"
        out.insert(3, warn_line)
    rows = {"Range Londra (in EM giornaliero)": [], "Ieri chiusura RTH": [], "Prezzo ora": [],
            "Gap ora vs chiusura di ieri": [], "Probabilità che il gap si chiuda in RTH": [],
            "EM 0DTE (straddle SPX)": [], "Dall'open: ±1 / ±1,5 / ±2 EM": []}
    for s in ("ES", "NQ"):
        r = today[s]
        _, px = last_bar(s)
        gap = None if px is None or r["prev_close"] is None else px - r["prev_close"]
        rows["Range Londra (in EM giornaliero)"].append(f"{n(r['london_range'], 2)} pt ({n(r['london_range_em'], 2)} EM)")
        rows["Ieri chiusura RTH"].append(n(r["prev_close"], 2))
        rows["Prezzo ora"].append(n(px, 2))
        if gap is not None and r["em"]:
            rate, cnt, label = gap_fill_rate(h, s, gap / r["em"])
            rows["Gap ora vs chiusura di ieri"].append(f"{n(gap, 2)} pt ({n(gap / r['em'], 2)} EM)")
            rows["Probabilità che il gap si chiuda in RTH"].append(f"**{n(rate, pct=True)}** ({label}, {cnt} giorni)")
        else:
            rows["Gap ora vs chiusura di ieri"].append("–")
            rows["Probabilità che il gap si chiuda in RTH"].append("–")
        if e is not None and px is not None:
            pts = e["em_pct"] * px
            if s == "NQ":
                pts *= (today["NQ"]["vxn"] or 0) / (today["ES"]["vix"] or 1)
            rows["EM 0DTE (straddle SPX)"].append(f"**{n(pts, 1)} pt** ({n(e['em_pct'] * 100, 2)}%)"
                                                   + (" stima × VXN/VIX" if s == "NQ" else ""))
            rows["Dall'open: ±1 / ±1,5 / ±2 EM"].append(f"±{n(pts, 0)} / ±{n(1.5 * pts, 0)} / ±{n(2 * pts, 0)}")
        else:
            rows["EM 0DTE (straddle SPX)"].append("–")
            rows["Dall'open: ±1 / ±1,5 / ±2 EM"].append("–")
    out += ["| | ES | NQ |", "|---|---|---|"] + [f"| {k} | {v[0]} | {v[1]} |" for k, v in rows.items()]

    r = today["ES"]
    low = r["gex_pct"] is not None and r["gex_pct"] < 0.3
    out += [""]
    if e is not None:
        out.append(f"- **EM 0DTE** dalla foto delle {rome(e['timestamp'])} "
                   f"({'prima' if e['pre_open'] else 'dopo'} l'apertura cash, {n(e['minutes_to_close'], 0)} minuti "
                   f"alla chiusura). Statistica Stucchi, verificata su ES: {EM_STUCCHI}.")
    out += [
        f"- **GEX** {it(r['gex_regime'])}, {n(r['gex_pct'], pct=True)} dell'anno"
        + (f" → **GEX basso: trend day {n(trend_rate(h, 'ES', True), pct=True)} contro "
           f"{n(trend_rate(h, 'ES', False), pct=True)}**." if low else "."),
        "- Il GEX da solo **non** accende il setup C (non regge sul 2024–oggi): serve l'accettazione fuori IB "
        "con CVD concorde (§5.1).",
    ]
    return "\n".join(out)


def main() -> None:
    session = sys.argv[1] if len(sys.argv) > 1 else ""
    if session not in ("london", "ny"):
        sys.exit("uso: contesto.py london|ny [--no-update]")
    warn = [] if "--no-update" in sys.argv else update(session)
    ctx = context()
    print(london(ctx, warn) if session == "london" else ny(ctx, warn))


if __name__ == "__main__":
    main()
