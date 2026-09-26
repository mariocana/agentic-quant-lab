# SPEC — ORB_Breakout (Stage 0)

**Ipotesi**: se NQ chiude sopra il range dei primi 30 minuti di cash session, il
movimento continua nella giornata abbastanza spesso da pagare uno stop al lato opposto
del range con target 1R.
**Perché**: flussi che possono operare solo dopo le 09:30 NY (fondi, algos benchmarked
alla sessione) + momentum intraday documentato (Market Intraday Momentum, JFE 2018;
Zarattini 2023). Chi perde: chi fade l'apertura. Edge validato dal corso su NQ 2021‑26
(823 trade, WR 58%, avg $183, PF 1.28).

| | |
|---|---|
| Famiglia | trend / breakout |
| Strumento · TF · sessione | @NQ · 5 min · Globex, chart in ora Chicago |
| Range | 08:30–09:00 CT |
| Entry | prima barra che chiude > range high (long only) |
| Stop | range low |
| Target | 1R |
| Time exit | 14:00 CT |
| Trade/giorno | 1 |
| Profilo prop | WR ~58%, R:R 1 → ok |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi (una volta sola).
**Varianti pre‑registrate (Stage 4)**: TP 0.5R; cutoff ingressi 11:00 CT; filtro delta
(UpTicks−DownTicks ≥ 200); `MaxRisk_USD` (salta range > 250 pt); short leg (atteso: no);
**ingresso su ritracciamento a VWAP ancorato al breakout** (1–1.5 SD, stop 2×ATR — dalla
live Quant VWAP, vedi `mc/strategies/Quant_VWAP/NOTES.md`; NON adottare il suo TP 3×,
incompatibile col profilo prop).
**Kill**: fallisce un gate della pipeline → cimitero. Non si ottimizza il range (30 min
è il modello validato; 60 min = variante IB, strategia separata). Nota di robustezza: in
una live indipendente l'ottimizzazione della durata del range su NQ ha il picco a 30–32
min e tiene out‑of‑sample → i 30 min stanno in un cluster, non su un picco fittato.

Stato: Stage 1 ✔ (report ES/NQ in `reports/`).
