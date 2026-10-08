"""Contesto automatico per la scheda di sessione (playbook Stucchi).

    contesto.py london   -> blocco per la scheda di Londra (prima delle 09:00)
    contesto.py ny       -> blocco per la scheda di NY (parte A, prima delle 15:30)

Prima aggiorna i dati (foto della catena scattate dal job Railway su R2,
VIX/GEX/NDX, barre MultiCharts, gold/daily_context; per NY anche una foto della
catena SPX adesso, per l'EM 0DTE), poi stampa in markdown un blocco che
sessioni/nuova_sessione.sh inserisce in cima alla scheda. --no-update salta
l'aggiornamento. I numeri vengono da quantlake.context_card, gli stessi della
pagina Contesto della dashboard.
"""
import sys
from datetime import datetime

from quantlake.context_card import ROME, SYMBOLS, card, update

IT = {"low": "bassa", "high": "alta", "up": "su", "down": "giù", "positive": "positivo", "negative": "negativo"}
EM_STUCCHI = "±1 EM toccato nel ~75% delle sessioni, oltre ±2 EM nel ~21%, chiusura entro ±2 EM nell'~89-91%"


def n(x, d=1, pct=False) -> str:
    """Numero all'italiana: 7.851,25 / 0,35 / 12%."""
    if x is None:
        return "–"
    if pct:
        return f"{x * 100:.0f}%"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def it(x: str | None) -> str:
    return "–" if x is None else IT.get(x, x)


def rome(ts: datetime | None) -> str:
    return "–" if ts is None else ts.astimezone(ROME).strftime("%d/%m %H:%M")


def table(rows: dict[str, list[str]]) -> list[str]:
    return ["| | ES | NQ |", "|---|---|---|"] + [f"| {k} | {v[0]} | {v[1]} |" for k, v in rows.items()]


def header(c: dict) -> list[str]:
    bars = ", ".join(f"{s} fino alle {rome(c['instruments'][s]['last_bar'])}" for s in SYMBOLS)
    out = [f"## 0. Contesto automatico (quantlake, {datetime.now(ROME):%H:%M})", "",
           f"Dati: barre {bars} · VIX/GEX della chiusura precedente · sessione del {c['session_date']:%d/%m}"]
    return out + [f"> ⚠ {w}" for w in c["warnings"]] + [""]


def gex_line(g: dict, extra: str) -> str:
    line = f"- **GEX** {it(g['gex_regime'])}, {n(g['gex_pct'], pct=True)} dell'anno"
    if g["gex_low"]:
        return line + (f" → **GEX basso: trend day {n(g['trend_rate_gex_low'], pct=True)} contro "
                       f"{n(g['trend_rate_gex_high'], pct=True)}.{extra}**")
    return line + (" → regime normale per i fade." if extra else ".")


def london(c: dict) -> str:
    i, g = c["instruments"], c["regime"]
    rows = {k: [] for k in ("Ieri RTH H / L / C", "EM giornaliero (VIX per ES, VXN per NQ)",
                            "Range Londra atteso p25 / p50 / p75", "Asia H / L (range)", "Prezzo ora",
                            "Mercato fermo se lo stop supera")}
    for s in SYMBOLS:
        x = i[s]
        rows["Ieri RTH H / L / C"].append(f"{n(x['prev_high'], 2)} / {n(x['prev_low'], 2)} / {n(x['prev_close'], 2)}")
        rows["EM giornaliero (VIX per ES, VXN per NQ)"].append(
            f"**{n(x['em'], 0)} pt** (IV {n(x['iv'])}, {n(x['iv_pct'], pct=True)} dell'anno)")
        rows["Range Londra atteso p25 / p50 / p75"].append(" / ".join(n(q, 0) for q in x["london_range_q"]) + " pt")
        rows["Asia H / L (range)"].append(f"{n(x['asia_high'], 2)} / {n(x['asia_low'], 2)} ({n(x['asia_range'], 2)})")
        rows["Prezzo ora"].append(n(x["price"], 2))
        rows["Mercato fermo se lo stop supera"].append(f"**{n(x['stop_max'], 1)} pt**")
    out = header(c) + table(rows) + [
        "",
        f"- **Volatilità** {it(g['vol_regime'])} ({n(g['iv_pct'], pct=True)} dell'anno), trend 20 giorni "
        f"{it(g['trend20'])} → quadrante `{g['quadrant'] or '–'}`. Term structure VIX9D/VIX {n(g['term_9d'], 2)}"
        f"{' → **stress a breve**' if (g['term_9d'] or 0) > 1 else ''}.",
        gex_line(g, " Interruttore trend day (§2.0) con un solo segnale."),
        "- **Mercato fermo** (§1.3): in un quarto delle mattine Londra fa meno del p25. Se il tuo stop è più "
        "grande del valore in tabella, l'oscillazione attesa non arriva a 2× lo stop: si guarda e basta.",
        "- Il regime della mattina (rotazionale o direzionale) non si prevede da questi numeri: si legge live "
        "dall'accettazione (§1.3).",
    ]
    return "\n".join(out)


def ny(c: dict) -> str:
    i, g, e = c["instruments"], c["regime"], c["em_0dte"]
    rows = {k: [] for k in ("Range Londra (in EM giornaliero)", "Ieri chiusura RTH", "Prezzo ora",
                            "Gap ora vs chiusura di ieri", "Probabilità che il gap si chiuda in RTH",
                            "EM 0DTE (straddle SPX)", "Dall'open: ±1 / ±1,5 / ±2 EM")}
    for s in SYMBOLS:
        x = i[s]
        rows["Range Londra (in EM giornaliero)"].append(f"{n(x['london_range'], 2)} pt ({n(x['london_range_em'], 2)} EM)")
        rows["Ieri chiusura RTH"].append(n(x["prev_close"], 2))
        rows["Prezzo ora"].append(n(x["price"], 2))
        if x["gap"] is not None:
            f = x["gap_fill"]
            label = f"{n(f['lo'], 2)}–{n(f['hi'], 2)} EM" if f["hi"] else f"> {n(f['lo'], 2)} EM"
            rows["Gap ora vs chiusura di ieri"].append(f"{n(x['gap'], 2)} pt ({n(x['gap_em'], 2)} EM)")
            rows["Probabilità che il gap si chiuda in RTH"].append(f"**{n(f['rate'], pct=True)}** ({label}, {f['days']} giorni)")
        else:
            rows["Gap ora vs chiusura di ieri"].append("–")
            rows["Probabilità che il gap si chiuda in RTH"].append("–")
        em0 = x["em_0dte"]
        if em0 is not None:
            rows["EM 0DTE (straddle SPX)"].append(f"**{n(em0, 1)} pt** ({n(e['em_pct'] * 100, 2)}%)"
                                                   + (" stima × VXN/VIX" if x["em_0dte_estimated"] else ""))
            rows["Dall'open: ±1 / ±1,5 / ±2 EM"].append(f"±{n(em0, 0)} / ±{n(1.5 * em0, 0)} / ±{n(2 * em0, 0)}")
        else:
            rows["EM 0DTE (straddle SPX)"].append("–")
            rows["Dall'open: ±1 / ±1,5 / ±2 EM"].append("–")
    out = header(c) + table(rows) + [""]
    if e is not None:
        out.append(f"- **EM 0DTE** dalla foto delle {rome(e['timestamp'])} "
                   f"({'prima' if e['pre_open'] else 'dopo'} l'apertura cash, {n(e['minutes_to_close'], 0)} minuti "
                   f"alla chiusura). Statistica Stucchi, verificata su ES: {EM_STUCCHI}.")
    out += [
        gex_line(g, ""),
        "- Il GEX da solo **non** accende il setup C (non regge sul 2024–oggi): serve l'accettazione fuori IB "
        "con CVD concorde (§5.1).",
    ]
    return "\n".join(out)


def main() -> None:
    session = sys.argv[1] if len(sys.argv) > 1 else ""
    if session not in ("london", "ny"):
        sys.exit("uso: contesto.py london|ny [--no-update]")
    warn = [] if "--no-update" in sys.argv else update(session)
    c = card()
    c["warnings"] = warn + c["warnings"]
    print(london(c) if session == "london" else ny(c))


if __name__ == "__main__":
    main()
