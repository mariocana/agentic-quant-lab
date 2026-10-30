"""Calibrazione delle regole di contesto del playbook Stucchi su gold/daily_context/1d.

Ogni regola è misurata su due periodi separati:
    IS   2016-2023  qui si guardano i dati e si scelgono le soglie
    OOS  2024-oggi  stesse soglie, nessun ritocco: la regola regge o no

Scrive education/enrico_stucchi/CALIBRAZIONE_contesto.md (tabelle rigenerate a
ogni lancio; i verdetti sono testo fisso, da rileggere se i numeri cambiano).

Run (dopo historical/daily_context.py):
    .venv/bin/python applications/research/calibrazione_contesto.py
"""
from datetime import date
from pathlib import Path

import polars as pl
from deltalake import DeltaTable

from quantlake.config import GOLD_ROOT

REPORT = Path(__file__).resolve().parents[4] / "education" / "enrico_stucchi" / "CALIBRAZIONE_contesto.md"
IS_END = 2023
GEX_LOW = 0.3   # gex_pct sotto il 30° percentile dell'ultimo anno
IV_HIGH = 0.5   # iv_pct sopra la mediana dell'ultimo anno


def load() -> pl.DataFrame:
    df = pl.from_arrow(DeltaTable(str(GOLD_ROOT / "daily_context" / "1d")).to_pyarrow_table())
    return df.filter("complete").sort("symbol", "date").with_columns(
        pl.when(pl.col("date").dt.year() <= IS_END).then(pl.lit("IS")).otherwise(pl.lit("OOS")).alias("periodo"),
        pl.when(pl.col("gex_pct") < GEX_LOW).then(pl.lit("basso")).when(pl.col("gex_pct").is_not_null())
        .then(pl.lit("alto")).alias("gex"),
        pl.when(pl.col("iv_pct") >= IV_HIGH).then(pl.lit("alta")).when(pl.col("iv_pct").is_not_null())
        .then(pl.lit("bassa")).alias("iv"),
        (pl.col("rth_high") - pl.col("rth_open")).alias("_up"),
        (pl.col("rth_open") - pl.col("rth_low")).alias("_dn"),
        (pl.col("rth_close") - pl.col("rth_open")).abs().alias("_oc"),
    )


def md(df: pl.DataFrame, pct: tuple[str, ...] = (), dec: tuple[str, ...] = ()) -> str:
    """Tabella markdown; colonne in pct come percentuali, in dec con 2 decimali."""
    def cell(c, v):
        if v is None:
            return "–"
        if c in pct:
            return f"{v * 100:.0f}%"
        if c in dec:
            return f"{v:.2f}"
        return str(v)
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(cell(c, r[c]) for c in df.columns) + " |" for r in df.iter_rows(named=True))


def em_touch(df: pl.DataFrame) -> str:
    out = []
    for col, label in (("em", "VIX/VXN ieri"), ("em_1d", "VIX1D ieri"), ("em_open", "VIX1D apertura (1σ)"),
                       ("em_stucchi", "0,7 × VIX1D apertura")):
        d = df.filter(pl.col(col).is_not_null())
        out.append(d.group_by("symbol", "periodo").agg(
            pl.lit(label).alias("EM da"),
            pl.len().alias("giorni"),
            (pl.max_horizontal("_up", "_dn") >= pl.col(col)).mean().alias("tocca ±1 EM"),
            (pl.max_horizontal("_up", "_dn") >= 2 * pl.col(col)).mean().alias("tocca ±2 EM"),
            (pl.col("_oc") <= 2 * pl.col(col)).mean().alias("chiude entro ±2 EM"),
            (pl.max_horizontal("_up", "_dn") / pl.col(col)).median().alias("escursione mediana (EM)"),
        ))
    t = pl.concat(out).sort("EM da", "symbol", "periodo")
    return md(t, pct=("tocca ±1 EM", "tocca ±2 EM", "chiude entro ±2 EM"), dec=("escursione mediana (EM)",))


def gex_iv(df: pl.DataFrame) -> str:
    t = df.filter(pl.col("gex").is_not_null() & pl.col("iv").is_not_null()).group_by(
        "symbol", "periodo", "iv", "gex"
    ).agg(
        pl.len().alias("giorni"),
        (pl.col("day_type") != "rotation").mean().alias("trend day"),
        pl.col("rth_range_em").median().alias("range RTH (EM)"),
    ).sort("symbol", "periodo", "iv", "gex")
    return md(t, pct=("trend day",), dec=("range RTH (EM)",))


def london(df: pl.DataFrame) -> tuple[str, str]:
    d = df.filter(pl.col("london_range") > 0).with_columns(
        (pl.col("london_move").abs() / pl.col("london_range")).alias("eff"),
        (pl.col("asia_range") / pl.col("range20")).cut([0.3, 0.5, 0.7], labels=["< 30%", "30–50%", "50–70%", "> 70%"])
        .alias("asia / ATR20"),
    )
    by_asia = d.filter(pl.col("range20").is_not_null()).group_by("symbol", "periodo", "asia / ATR20").agg(
        pl.len().alias("giorni"),
        (pl.col("eff") >= 0.7).mean().alias("Londra direzionale"),
        pl.col("eff").mean().alias("efficienza media"),
        pl.col("london_range_em").median().alias("range Londra (EM)"),
    ).sort("symbol", "periodo", "asia / ATR20")
    q = df.filter(pl.col("london_range_em").is_not_null()).group_by("symbol", "periodo").agg(
        *[pl.col("london_range_em").quantile(p).alias(f"p{int(p * 100)}") for p in (0.1, 0.25, 0.5, 0.75, 0.9)],
        pl.col("em").median().alias("EM mediano (pt)"),
    ).sort("symbol", "periodo")
    return (md(by_asia, pct=("Londra direzionale",), dec=("efficienza media", "range Londra (EM)")),
            md(q, dec=("p10", "p25", "p50", "p75", "p90", "EM mediano (pt)")))


def ib_follow(df: pl.DataFrame) -> str:
    d = df.filter(pl.col("ib_break").is_in(["up", "down"]) & pl.col("gex").is_not_null()).with_columns(
        pl.when(pl.col("ib_break") == "up").then(pl.col("rth_close") > pl.col("ib_high"))
        .otherwise(pl.col("rth_close") < pl.col("ib_low")).alias("follow"),
        pl.when(pl.col("ib_break") == "up").then(pl.col("rth_close") - pl.col("ib_high"))
        .otherwise(pl.col("ib_low") - pl.col("rth_close")).truediv(pl.col("em")).alias("ext"),
    )
    t = d.group_by("symbol", "periodo", "gex").agg(
        pl.len().alias("giorni"),
        pl.col("follow").mean().alias("chiude oltre l'IB"),
        pl.col("ext").mean().alias("chiusura oltre IB (EM, media)"),
    ).sort("symbol", "periodo", "gex")
    return md(t, pct=("chiude oltre l'IB",), dec=("chiusura oltre IB (EM, media)",))


def moc(df: pl.DataFrame) -> str:
    d = df.filter(pl.col("moc_move").is_not_null() & (pl.col("moc_move") != 0))
    defs = {
        "apertura RTH → 14:50 CT": pl.col("moc_open") - pl.col("rth_open"),
        "chiusura di ieri → 14:50 CT": pl.col("moc_open") - pl.col("prev_close"),
    }
    rows = []
    for name, expr in defs.items():
        x = d.with_columns(expr.alias("dir")).filter(pl.col("dir") != 0)
        rows.append(x.group_by("symbol", "periodo").agg(
            pl.lit(name).alias("direzione della giornata"),
            pl.len().alias("giorni"),
            (pl.col("moc_move").sign() == pl.col("dir").sign()).mean().alias("MOC nella stessa direzione"),
            ((pl.col("dir").abs() / pl.col("em")) >= 0.5).mean().alias("giorni con movimento ≥ 0,5 EM"),
        ))
        big = x.filter((pl.col("dir").abs() / pl.col("em")) >= 0.5)
        rows.append(big.group_by("symbol", "periodo").agg(
            pl.lit(name + ", solo movimento ≥ 0,5 EM").alias("direzione della giornata"),
            pl.len().alias("giorni"),
            (pl.col("moc_move").sign() == pl.col("dir").sign()).mean().alias("MOC nella stessa direzione"),
            pl.lit(None, pl.Float64).alias("giorni con movimento ≥ 0,5 EM"),
        ))
    t = pl.concat(rows).sort("direzione della giornata", "symbol", "periodo")
    return md(t.select("direzione della giornata", "symbol", "periodo", "giorni", "MOC nella stessa direzione"),
              pct=("MOC nella stessa direzione",))


def gap(df: pl.DataFrame) -> str:
    t = df.filter(pl.col("gap_filled").is_not_null() & pl.col("gap_em").is_not_null()).with_columns(
        pl.col("gap_em").abs().cut([0.1, 0.25, 0.5, 1.0], labels=["< 0,1", "0,1–0,25", "0,25–0,5", "0,5–1", "> 1"])
        .alias("gap in EM (assoluto)")
    ).group_by("symbol", "periodo", "gap in EM (assoluto)").agg(
        pl.len().alias("giorni"), pl.col("gap_filled").mean().alias("gap chiuso in RTH"),
    ).sort("symbol", "gap in EM (assoluto)", "periodo")
    return md(t, pct=("gap chiuso in RTH",))


def main() -> None:
    df = load()
    n = df.group_by("symbol").agg(pl.len(), pl.col("date").min().alias("da"), pl.col("date").max().alias("a")).sort("symbol")
    span = ", ".join(f"{r['symbol']} {r['len']:,} giorni ({r['da']} → {r['a']})" for r in n.iter_rows(named=True))
    by_asia, lon_q = london(df)
    text = f"""# Calibrazione del contesto giornaliero

Generato da `python/quantlake/applications/research/calibrazione_contesto.py` il {date.today()}
su `gold/daily_context/1d`: {span}.

**Metodo.** IS = 2016–2023, dove si guardano i dati e si scelgono le soglie. OOS =
2024–oggi, stesse soglie senza ritocchi. Una regola entra nel playbook solo se va nella
stessa direzione in entrambi i periodi. EM = chiusura cash di ieri (SPX / NDX) × VIX
(VXN per NQ) / √252, in punti, salvo dove indicato (sezione 1 confronta le definizioni;
quelle da VIX1D solo ES, da maggio 2022). L'EM da VIX è ~2,5× quello di Stucchi: i
multipli di EM delle sezioni 2–6 sono su quella scala. Trend day =
chiusura nel 15% estremo del range RTH **e** range ≥ 1 EM (definizione provvisoria).
GEX basso = sotto il 30° percentile dell'ultimo anno (SqueezeMetrics, chiusura di ieri);
IV alta = sopra la mediana dell'ultimo anno. RTH = 08:30–15:00 Chicago (15:30–22:00
Roma), Londra = 09:00–13:30 Roma.

## Verdetti (dati al 2026-10-08)

| Regola / ipotesi | Verdetto | Cosa cambia |
|---|---|---|
| Stucchi (SPX RTH 2017–2025): ±1 EM toccato nel ~75% delle sessioni, oltre ±2 EM nel ~21%, chiusura entro ±2 EM nell'~89% | **Si ritrova su ES, con il suo EM**: 0,7 × (SPX all'apertura × VIX1D di apertura / √252), escursione misurata dall'apertura RTH → 75% / 21% / ~90%. È circa lo straddle ATM 0DTE all'apertura. Con EM da 1σ (la formula `VIX1D_open / 15.87` del playbook) i numeri scendono a ~48% / 6% / 97%; con VIX ~20% / 1% / 99% | Nel playbook l'EM va definito come il suo (`em_stucchi`, ~0,4 × l'EM da VIX): tutti i multipli di EM che cita (target 1,5–2 EM del setup C) sono su questa scala |
| GEX basso → più trend day e range più ampio | **Confermata** in IS e OOS, anche a parità di IV: con IV alta i trend day passano da ~15% a ~25–30% (ES OOS più debole) | Filtro valido per **spegnere** i fade (A, B) e per il sistematico, non un segnale d'ingresso |
| Setup C: GEX basso → l'IB rotto da un lato prosegue | **Non confermata.** Vantaggio in IS (74% contro 66%) che sparisce in OOS (~60% in entrambi) | Il filtro GEX del setup C non va usato come unica condizione: serve l'accettazione fuori IB vista live |
| §1.3: range asiatico < 50% ATR → mattina rotazionale | **Nessun potere predittivo**: la quota di Londra direzionale è ~15–20% in ogni fascia | Togliere la soglia numerica: il regime di Londra si legge live (accettazione), non dai numeri pre-sessione |
| Mercato fermo (oscillazione attesa < 2× stop) | Misurabile: range Londra mediano ~0,35 EM da VIX (p25 ~0,25), stabile IS→OOS | Regola concreta: se 0,25 × EM da VIX < 2 × stop → mattina da guardare e basta (EM da VIX perché è noto alle 09:00) |
| Stucchi: negli ultimi 10 minuti la direzione resta quella del giorno il 75% delle volte | **Non si ritrova**: ~45–51% con ogni definizione testata, anche su giornate con movimento ≥ 0,5 EM | Nessun trade MOC su questa base; la statistica va chiarita alla fonte |
| Gap: probabilità di chiusura in RTH | **Forte e stabile**: decresce con la dimensione del gap in EM (≈93% sotto 0,1 EM, ≈50% a 0,25–0,5, ≈15% sopra 1 EM) | Tabella utilizzabile come contesto per NY, da mettere nella scheda |

Nota: il trend day è misurato con la chiusura, quindi non si usa per prevedere il MOC
(sarebbe circolare).

## 1. Expected Move: quanto si muove davvero il prezzo dall'apertura RTH

{em_touch(df)}

## 2. GEX e volatilità implicita → trend day

{gex_iv(df)}

## 3. Londra

### 3.1 Il range asiatico prevede una Londra direzionale?

Londra direzionale = |chiusura − apertura| ≥ 70% del range della sessione.

{by_asia}

### 3.2 Range di Londra in multipli di EM (per la regola del mercato fermo)

{lon_q}

Esempio: con EM ES = 74 punti, metà delle mattine fa meno di ~0,33 × 74 ≈ 24 punti di
range totale, un quarto meno di ~18.

## 4. NY: IB rotto da un solo lato, e prosegue?

{ib_follow(df)}

## 5. MOC: gli ultimi 10 minuti (14:50–15:00 CT) vanno nella direzione del giorno?

{moc(df)}

## 6. Gap all'apertura RTH: si chiude?

{gap(df)}
"""
    REPORT.write_text(text)
    print(f"scritto {REPORT}")


if __name__ == "__main__":
    main()
