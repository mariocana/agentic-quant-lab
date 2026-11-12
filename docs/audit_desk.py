"""I numeri di docs/audit_2026-11-12.md.

    cd alpha-quant && PYTHONHASHSEED=1 poetry run python ../docs/audit_desk.py

PYTHONHASHSEED fissato perche il replay non e riproducibile al bit senza: l'ordine
degli intent in desk/signals/rebalance.py viene da un set di stringhe (sezione 3).

Non scrive nel registro delle prove e non apre l'holdout: i replay girano solo sul
periodo di validation di reversal_v1, una spec gia giudicata (FAIL il 10/11/2026),
con HistoricalMarket bloccato sull'holdout come sempre. Nessuna nuova spec viene
giudicata qui: sono varianti del modello di esecuzione, non della strategia.

Sezioni:
  1  journal locale del desk (testnet, 07-15/10/2026): ordini maker eseguiti, stop piazzati
  2  le regole sulla perdita giornaliera con un ciclo al giorno
  3  replay di validation: halt, costi tutti taker, maker eseguiti a meta
  4  potenza dei gate validation + holdout per Sharpe vero e per k
  5  liquidita su Hyperliquid (un campione del registro di mercato)
  6  profondita dello storico per strategie intraday
"""
from __future__ import annotations

import collections
import json
import logging
import math
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
from deltalake import DeltaTable

from alphaquant.config import QUANTLAKE_DATA_ROOT
from alphaquant.engine.desk_replay import HistoricalMarket, replay, splits
from alphaquant.engine.desk_trades import to_simresult
from alphaquant.validation.portfolio import (
    PERIODS_PER_YEAR, PortfolioGateConfig, PortfolioMetrics, deflated_sharpe, measure_portfolio,
)
from desk.config import load_limits
from desk.execution.paper import PaperAdapter
from desk.risk.state import RiskState
from desk.signals.reversal import Reversal

LAB = Path(__file__).resolve().parents[1]
JOURNAL = LAB / "trading-desk" / "var" / "journal.jsonl"
LIVE_FROM = "2026-10-07"                 # primo ciclo su testnet nel journal locale
ROOT = Path(QUANTLAKE_DATA_ROOT)


def titolo(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# ---- 1. journal ---------------------------------------------------------------

def journal() -> None:
    titolo("1. Journal locale del desk (testnet)")
    if not JOURNAL.exists():
        print("trading-desk/var/journal.jsonl non c'e (var/ e ignorata da git): sezione saltata")
        return
    rows = [json.loads(x) for x in JOURNAL.read_text().splitlines() if x.strip()]
    intents = [r for r in rows if r["kind"] == "intent" and r["ts"] >= LIVE_FROM]
    verdict = {r["intent_id"]: r for r in rows if r["kind"] == "verdict"}
    fills = collections.defaultdict(list)
    for r in rows:
        if r["kind"] in ("fill", "fill_reconciled"):
            fills[r["intent_id"]].append(r)
    print(f"periodo {intents[0]['ts'][:10]} -> {intents[-1]['ts'][:10]}, {len(intents)} intent")
    for tipo in ("limit_alo", "limit_ioc"):
        ok = [i for i in intents if i["order_type"] == tipo
              and verdict.get(i["id"], {}).get("decision") in ("approve", "reduce")]
        presi = [i for i in ok if fills.get(i["id"])]
        chiesto = sum(verdict[i["id"]]["approved_notional_usd"] for i in ok)
        avuto = sum(x["filled_usd"] for i in presi for x in fills[i["id"]])
        print(f"  {tipo:10} approvati {len(ok):3}  eseguiti {len(presi):3} ({len(presi) / max(len(ok), 1):.0%})"
              f"  nozionale {avuto:,.0f} su {chiesto:,.0f} ({avuto / max(chiesto, 1):.0%})")
    con_stop = [i for i in intents if i.get("stop_px")]
    eseguiti = [i for i in con_stop if fills.get(i["id"])]
    stop_messi = sum(1 for fs in fills.values() for f in fs if f.get("stop_oid"))
    print(f"  intent con stop_px {len(con_stop)}, di cui eseguiti {len(eseguiti)}; "
          f"fill con uno stop sull'exchange: {stop_messi}")


# ---- 2. regole giornaliere ------------------------------------------------------

def regole_giornaliere(limits: dict) -> None:
    titolo("2. Perdita giornaliera con un ciclo al giorno (RiskState.observe)")
    with tempfile.TemporaryDirectory() as d:
        st = RiskState.load(Path(d) / "risk.json")
        t = lambda g: datetime(2026, 1, g, 0, 5, tzinfo=timezone.utc)   # noqa: E731
        print("  equity al ciclo delle 00:05, tre giorni di fila; ogni giorno -6%")
        for g, eq in ((1, 10_000.0), (2, 9_400.0), (3, 8_836.0)):
            fired = st.observe(eq, limits, now=t(g))
            print(f"    giorno {g}: equity {eq:>8,.0f}  day_pnl visto {st.day_pnl_pct(eq):+.2%}  regole {fired or '-'}")
        print(f"  soglie: freeze {limits['daily_loss_freeze_pct']:.0%}, flatten {limits['daily_loss_flatten_pct']:.0%}, "
              f"drawdown {limits['max_drawdown_pct']:.0%}")
        st2 = RiskState.load(Path(d) / "risk2.json")
        st2.observe(10_000.0, limits, now=t(1))
        fired = st2.observe(9_400.0, limits, now=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc))
        print(f"  stesso -6% letto alle 12:00 dello stesso giorno: regole {fired}")


# ---- 3. replay ------------------------------------------------------------------

class MakerAMeta(PaperAdapter):
    """Un ordine post-only viene eseguito con probabilita P, altrimenti resta sul
    book e il ciclo dopo lo cancella e lo ripropone: quello che fa il desk live."""
    P = 0.5
    rng = random.Random(0)

    def execute(self, intent, verdict, mid_px):
        if intent.order_type == "limit_alo" and self.rng.random() > self.P:
            return None
        return super().execute(intent, verdict, mid_px)


def _riga(nome: str, res) -> None:
    m = measure_portfolio(to_simresult(res), res.start_equity)
    eq = np.concatenate([[res.start_equity], res.equity["equity"].to_numpy()])
    r = eq[1:] / eq[:-1] - 1
    halt = next((j["ts"][:10] for j in res.journal if j["kind"] == "cycle" and j["state_rules"]), "-")
    freeze = sum(1 for j in res.journal if j["kind"] == "verdict" and "daily_loss_freeze" in j["rules_fired"])
    attivi = sum(1 for j in res.journal if j["kind"] == "cycle" and j["fills"])
    print(f"  {nome:34} {m.total_return:+7.1%} {m.sharpe:+6.2f} {m.max_dd:6.1%} {m.fees:7.0f} {m.funding:+7.0f} "
          f"{m.trades:5} {halt:>10} {attivi:4} {(r <= -0.03).sum():3} {freeze:3}")


def replay_varianti(limits: dict) -> None:
    titolo("3. reversal_v1 sul periodo di validation, con il ciclo del desk")
    market = HistoricalMarket.from_quantlake()            # holdout chiuso
    start, end = splits()["validation"]
    print(f"  {start:%Y-%m-%d} -> {end:%Y-%m-%d}, 10.000 di equity, un ciclo al giorno alle 00:05")
    print(f"  {'variante':34} {'rend.':>7} {'Sharpe':>6} {'maxDD':>6} {'fee':>7} {'funding':>7} {'trade':>5} "
          f"{'halt':>10} {'gg+':>4} {'<-3%':>3} {'frz':>3}")
    taker = PaperAdapter.COSTS["taker"]
    senza_halt = {**limits, "max_drawdown_pct": 1.0}
    _riga("come il verdetto del 10/11", replay(Reversal(), market, limits, start, end))
    _riga("senza halt di drawdown", replay(Reversal(), market, senza_halt, start, end))
    _riga("tutto taker (4,5 + 7,3 bps)", replay(Reversal(), market, limits, start, end,
                                                 costs={"maker": taker, "taker": taker}))
    _riga("tutto taker, senza halt", replay(Reversal(), market, senza_halt, start, end,
                                             costs={"maker": taker, "taker": taker}))
    with patch("alphaquant.engine.desk_replay.PaperAdapter", MakerAMeta):
        esiti = []
        for seed in range(12):
            MakerAMeta.rng = random.Random(seed)
            res = replay(Reversal(), market, limits, start, end)
            m = measure_portfolio(to_simresult(res), res.start_equity)
            esiti.append((m.total_return, m.sharpe))
    rend, sh = sorted(x[0] for x in esiti), sorted(x[1] for x in esiti)
    print(f"  maker eseguiti al 50%, 12 sorteggi: rendimento da {rend[0]:+.1%} a {rend[-1]:+.1%} "
          f"(mediana {rend[6]:+.1%}), Sharpe da {sh[0]:+.2f} a {sh[-1]:+.2f}")
    print("  gg+ = cicli con almeno un fill; <-3% = giorni con equity -3% o peggio; "
          "frz = verdetti daily_loss_freeze")


# ---- 4. potenza dei gate --------------------------------------------------------

def potenza_gate(n: int = 4000, seed: int = 11) -> None:
    titolo("4. Quante strategie passano validation + holdout, per Sharpe vero")
    cfg = PortfolioGateConfig()
    s = splits()
    t_val = (s["validation"][1] - s["validation"][0]).days + 1
    t_hold = (s["holdout"][1] - s["holdout"][0]).days + 1
    print(f"  validation {t_val} giorni, holdout {t_hold} giorni, {n} simulazioni per cella, rendimenti "
          "giornalieri normali\n  (il gate sul drawdown non e simulato: dipende dalla volatilita, non dallo Sharpe)")
    print(f"  {'Sharpe vero':>11} | " + " | ".join(f"{'k=' + str(k):^29}" for k in (1, 5, 20)))
    print(f"  {'':>11} | " + " | ".join(f"{'valid.':>7} {'entrambi':>8} {'Sh. visto':>10}" for _ in range(3)))
    rng = np.random.default_rng(seed)
    sd = 0.01
    for true in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0):
        mu = true / math.sqrt(PERIODS_PER_YEAR) * sd
        cells = []
        for k in (1, 5, 20):
            v = rng.normal(mu, sd, (n, t_val))
            h = rng.normal(mu, sd, (n, t_hold))
            pv = pb = 0
            visti = []
            for i in range(n):
                r = v[i]
                srd = r.mean() / r.std(ddof=1)
                z = (r - r.mean()) / r.std(ddof=1)
                m = PortfolioMetrics(days=t_val, trades=500, total_return=float(np.prod(1 + r) - 1),
                                     sharpe=srd * math.sqrt(PERIODS_PER_YEAR), sharpe_daily=srd,
                                     skew=float((z ** 3).mean()), kurtosis=float((z ** 4).mean()),
                                     max_dd=0.0, gross_pnl=1.0, fees=0.0, funding=0.0, cost_share=0.0)
                if not (m.sharpe > 0 and deflated_sharpe(m, k) >= cfg.min_deflated):
                    continue
                pv += 1
                visti.append(m.sharpe)
                rh = h[i]
                sh = rh.mean() / rh.std(ddof=1) * math.sqrt(PERIODS_PER_YEAR)
                if np.prod(1 + rh) > 1 and sh > 0 and sh >= cfg.holdout_min_sharpe_ratio * m.sharpe:
                    pb += 1
            visto = f"{np.mean(visti):10.2f}" if visti else f"{'-':>10}"
            cells.append(f"{pv / n:7.1%} {pb / n:8.1%} {visto}")
        print(f"  {true:11.1f} | " + " | ".join(cells))
    print("  Sh. visto = Sharpe medio misurato in validation dalle strategie che la passano")


def soglia_prossima() -> None:
    """Lo Sharpe annuo minimo che passa il deflated Sharpe, risolto per bisezione."""
    from alphaquant.registry import Registry
    s = splits()
    t_val = (s["validation"][1] - s["validation"][0]).days + 1
    annui = Registry().validation_sharpes()
    prior = [x / math.sqrt(PERIODS_PER_YEAR) for x in annui]

    def m(sa: float) -> PortfolioMetrics:
        return PortfolioMetrics(t_val, 500, 0.1, sa, sa / math.sqrt(PERIODS_PER_YEAR), 0.0, 3.0, 0.0, 1.0, 0.0, 0.0, 0.0)

    def soglia(f) -> float:
        lo, hi = 0.0, 60.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if f(mid) >= 0.95 else (mid, hi)
        return hi

    print(f"\n  Sharpe annuo minimo in validation (rendimenti normali, {t_val} giorni); nel registro: {annui}")
    print(f"    k=1                                          {soglia(lambda x: deflated_sharpe(m(x), 1)):.2f}")
    k = len(annui) + 1
    come = soglia(lambda x: deflated_sharpe(m(x), k, prior + [m(x).sharpe_daily]))
    print(f"    prossima spec (k={k}), come la calcola evaluate  {come:.2f}")
    for kk in (2, 5, 10, 20):
        print(f"    k={kk:<2} con la varianza dello stimatore          {soglia(lambda x: deflated_sharpe(m(x), kk)):.2f}")


# ---- 5. liquidita ---------------------------------------------------------------

def liquidita() -> None:
    titolo("5. Liquidita su Hyperliquid (bronze/hyperliquid_market)")
    m = pl.from_arrow(DeltaTable(str(ROOT / "bronze" / "hyperliquid_market")).to_pyarrow_table())
    n = m["timestamp"].n_unique()
    print(f"  {n} campione/i, da {m['timestamp'].min():%Y-%m-%d %H:%M} a {m['timestamp'].max():%Y-%m-%d %H:%M} UTC")
    m = m.filter(~pl.col("is_delisted") & pl.col("mid_px").is_not_null()).with_columns(
        meta_spread=(pl.col("impact_ask_px") - pl.col("impact_bid_px")) / pl.col("mid_px") / 2 * 1e4,
        oi_usd=pl.col("open_interest") * pl.col("mark_px"))
    g = m.group_by("dex", "asset").agg(vol=pl.col("day_ntl_vlm").median(), oi=pl.col("oi_usd").median(),
                                       bps=pl.col("meta_spread").median(), funding=pl.col("funding").median())
    per_dex = g.group_by("dex").agg(perp=pl.len(), vol=pl.col("vol").sum(),
                                    sopra_10m=(pl.col("vol") >= 1e7).sum()).sort("vol", descending=True)
    print("  per dex: perp quotati, volume 24h totale, perp sopra 10 milioni al giorno")
    for r in per_dex.head(4).iter_rows(named=True):
        print(f"    {r['dex']:6} {r['perp']:4}  {r['vol'] / 1e9:6.2f} mld  {r['sopra_10m']:3}")
    nomi = ["BTC", "ETH", "SOL", "xyz:XYZ100", "xyz:SP500", "xyz:GOLD", "xyz:CL"]
    print(f"  {'perp':12} {'volume 24h':>12} {'open interest':>14} {'mezzo spread*':>14} {'funding/h':>10}")
    for a in nomi:
        r = g.filter(pl.col("asset") == a)
        if r.is_empty():
            print(f"  {a:12} non nel campione")
            continue
        r = r.row(0, named=True)
        print(f"  {a:12} {r['vol'] / 1e6:9,.0f} mln {r['oi'] / 1e6:11,.0f} mln {r['bps']:10.2f} bps {r['funding']:+10.4%}")
    top = g.filter((pl.col("dex") == "main") & (pl.col("vol") >= 1e7)).sort("vol", descending=True).head(40)
    print(f"  universo di reversal_v1 (dex principale, sopra 10 mln, al massimo 40): {top.height} perp; "
          f"l'ultimo fa {top['vol'].min() / 1e6:.0f} mln al giorno; mezzo spread* mediano "
          f"{top['bps'].median():.1f} bps, peggiore {top['bps'].max():.1f} bps")
    print("  * (impact ask - impact bid) / 2 sul mid: il costo di un ordine a mercato della size di "
          "riferimento dell'exchange")


# ---- 6. storia ------------------------------------------------------------------

def storia() -> None:
    titolo("6. Storico disponibile per una strategia intraday")

    def campo(tabella: str, simboli: list[str]):
        t = pl.from_arrow(DeltaTable(str(ROOT / tabella)).to_pyarrow_table(columns=["symbol", "timestamp"]))
        return t.filter(pl.col("symbol").is_in(simboli)).group_by("symbol").agg(
            da=pl.col("timestamp").min(), a=pl.col("timestamp").max(), barre=pl.len()).sort("symbol")

    for tabella, simboli in (("bronze/hyperliquid_ohlcv_1d", ["BTC", "xyz:XYZ100", "xyz:GOLD"]),
                             ("bronze/hyperliquid_ohlcv_1h", ["BTC", "xyz:XYZ100", "xyz:GOLD"]),
                             ("bronze/binance_um_ohlcv", ["BTCUSDT"])):
        for r in campo(tabella, simboli).iter_rows(named=True):
            print(f"  {tabella:30} {r['symbol']:11} {r['da']:%Y-%m-%d} -> {r['a']:%Y-%m-%d}  {r['barre']:>9,} barre")
    print("  Hyperliquid serve solo le ultime ~5000 barre per intervallo: a 5 minuti sono 17 giorni.")


if __name__ == "__main__":
    logging.getLogger("desk").setLevel(logging.ERROR)
    limits = load_limits()
    journal()
    regole_giornaliere(limits)
    replay_varianti(limits)
    potenza_gate()
    soglia_prossima()
    liquidita()
    storia()
