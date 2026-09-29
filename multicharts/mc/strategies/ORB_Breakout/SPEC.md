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
(UpTicks−DownTicks ≥ 200); `MaxRisk_USD` (vedi griglia sotto); short leg (atteso: no);
**ingresso su ritracciamento a VWAP ancorato al breakout** (1–1.5 SD, stop 2×ATR — dalla
live Quant VWAP, vedi `mc/strategies/Quant_VWAP/NOTES.md`; NON adottare il suo TP 3×,
incompatibile col profilo prop).
**Kill**: fallisce un gate della pipeline → cimitero. Non si ottimizza il range (30 min
è il modello validato; 60 min = variante IB, strategia separata). Nota di robustezza: in
una live indipendente l'ottimizzazione della durata del range su NQ ha il picco a 30–32
min e tiene out‑of‑sample → i 30 min stanno in un cluster, non su un picco fittato.

Stato: Stage 1 ✔ (report ES/NQ in `reports/`).

## Stage 4 — `MaxRisk_USD`: griglia e criterio, scritti prima del run (29/09/2026)

Il valore «250 pt» pre‑registrato allo Stage 0 era una stima al buio: sullo storico vero
salta **3 trade su 395**, quindi non cambierebbe niente. L'input resta quello
pre‑registrato; qui si fissa la griglia, come previsto dallo Stage 4.

**Distribuzione del range di apertura** (= distanza dello stop) sull'IS 2020‑2024,
ricostruita dalle uscite in SL e TP del run base:

| | punti | rischio 1 NQ | 1 micro | % trade saltati |
|---|---|---|---|---|
| mediana | 90 | $1.805 | $180 | — |
| p80 | 125 | $2.495 | $250 | 20% |
| p90 | 154 | $3.080 | $308 | 11% |
| p95 | 188 | $3.765 | $376 | 4% |
| p99 | 240 | $4.790 | $479 | 1% |
| max | 334 | $6.680 | $668 | — |

**Griglia**: `0` (base case) · `2500` · `3000` · `4000` · `5000`. Passi larghi, cinque
punti. Sotto $2.500 si salterebbe oltre un terzo dei trade: non è più togliere la coda,
è un'altra strategia.

**Come si gira** (deciso 29/09, prima dei risultati): tre **ottimizzazioni**, una per
periodo (IS intero, 1ª metà, 2ª metà), con `MaxRisk_USD` da **2500 a 5000 step 500**. Il
base case `0` è già misurato. I valori intermedi (3500, 4500) servono a **giudicare la
forma della curva** per il criterio del cluster, **non** a scegliere il migliore: la
decisione resta ancorata ai valori dichiarati sopra. Se un intermedio fosse il massimo
assoluto ma i dichiarati adiacenti fossero mediocri, la variante si scarta.

**Criterio di scelta, fissato ora**:
1. deve migliorare l'avg trade in **entrambe** le metà dell'IS (2020‑01→2022‑06 e
   2022‑07→2024‑12), non solo nel totale;
2. `n` deve restare ≥ 200;
3. si sceglie un valore **in un cluster**: se due soglie adiacenti funzionano e quella in
   mezzo no, il risultato è rumore e la variante si scarta;
4. non si scende sotto $2.500 nemmeno se i numeri migliorassero.

**Cosa può e non può fare** — scritto prima per non raccontarsela dopo:
- **può** sistemare il criterio sul peggior trade, per costruzione: con soglia $4.000 la
  perdita massima diventa $4.000, cioè $400 per micro, sotto il limite di $500;
- **probabilmente non può** sistemare il drawdown. Servirebbe passare da $36.290 a
  < $12.500, un terzo. Ma quel DD non è un trade mostruoso: è una **serie di perdite
  normali** a marzo 2020, e tagliare la coda non toglie una serie perdente;
- **gioca contro**: con `TP_RR 1.0` il target è largo quanto il range, quindi saltare i
  giorni a range largo elimina anche le **vincite più grosse**. L'effetto sul PF è
  genuinamente incerto e potrebbe essere negativo.

**Contesto del gate**: `DD ÷ 10 = $3.629` contro il max drawdown Apex di **$2.500**. Così
com'è, anche a 1 solo micro la strategia avrebbe fatto saltare un conto funded nel marzo
2020. La soglia del gate non è arbitraria: è la regola del conto.
