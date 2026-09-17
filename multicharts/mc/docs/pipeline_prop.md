# Pipeline PROP — strategie per passare l'eval e incassare i payout

Obiettivo unico di questa fase: **strategie che passano una eval prop e portano al
payout**. Non capitale proprio, non "trovare l'edge del secolo". Il resto aspetta.

Come una pipeline CI: ogni stage ha un **gate**. Se il gate fallisce, la strategia si
ferma lì (o torna allo stage 4 se il problema è correggibile senza toccare l'OOS).
Niente eccezioni "però l'equity è bella".

Profilo target (Lezione 10, Live 1–4): **win rate ≥ 55–60%, R:R 0.5–1**, trade frequenti,
DD per micro contratto piccolo rispetto al limite della prop. Sviluppo sempre su **NQ
(o contratto pieno) a 1 contratto**; la size in micro la decide il simulatore.

Regole prop di riferimento (Apex 50k, EOD trailing): target **$3.000**, max DD
**$2.500**, daily loss $1.000, 21 giorni, max 6 mini / 60 micro, min $150/giorno,
payout 100% dei primi $25k, ladder totale ~$13k per account.

---

## Stage 0 — Spec (prima di scrivere codice)
Scrivi in `mc/strategies/<nome>/SPEC.md`:
- ipotesi in una frase + **perché** dovrebbe funzionare (chi perde soldi contro di noi);
- famiglia (trend / mean reverting / evento), strumento, TF, sessione;
- entry, exit (TP/SL fissi o in R, time exit), un trade/giorno o max N;
- **date IS e OOS** (80/20) e criteri di kill, **decisi ora**.

**Gate 0**: tutto scritto. Nessuna spec = nessun codice.

## Stage 1 — Codice e meccanica
Signal PowerLanguage, flag 0/1, 1 contratto, ~100 giorni di dati, `ShowLog`.
Controllo su chart + List of Trades: trade dove previsto, un trade/giorno, flat all'ora
prevista, SL/TP = quelli della spec, con 10 contratti P&L ×10, nessun trade nel weekend
non voluto (half‑day: annotare).

**Gate 1**: meccanica corretta al 100%. Report salvato in `reports/`.

## Stage 2 — Backtest IS (1 contratto, costi on)
Costi: $2.50/lato + 1 tick. Solo il periodo IS.

**Gate 2** (tutti):
| Metrica | Soglia |
|---|---|
| n. trade IS | ≥ 200 |
| avg trade netto | ≥ soglia strumento (NQ $70 → MNQ $7; GC $140) |
| profit factor | ≥ 1.2 |
| win rate | ≥ 55% (profilo prop) |
| R:R nominale | 0.5–1 |
| max DD 1 contratto ÷ 10 (micro) | ≤ 50% del DD prop (Apex 50k: ≤ $1.250) |
| peggior trade ÷ 10 | ≤ 50% daily loss (≤ $500) |
| tabella annuale | nessun anno > 50% del profitto; segno stabile 2021‑23 vs 2024+ |

## Stage 3 — Monte Carlo built‑in (IS)
Reshuffle 1000 sim, 100% trade; Distribution analysis.

**Gate 3**: mediana net profit > 0; < 10% simulazioni in perdita; DD 95° perc. ÷ 10
≤ DD prop ($2.500).

## Stage 4 — Miglioramenti (solo IS)
Base case = versione senza filtri. Ogni aggiunta deve avere una ragione e passare lo
**split‑sample** (due metà dell'IS, migliora l'avg trade in entrambe). Ottimizzazione
a due passi, ≤ 3 input, step larghi, fitness PF; si sceglie il cluster.
Per il profilo prop: testare TP 0.5R vs 1R, cutoff ingressi, `MaxRisk_USD` (salta i
giorni in cui 1 micro rischia troppo).

**Gate 4**: regole semplici e spiegabili; ≤ 3 input ottimizzati; rifare Gate 2 e 3.

## Stage 5 — Out‑of‑sample (una volta)
Parametri congelati sull'OOS.

**Gate 5**: avg trade, WR, PF nello stesso ordine di grandezza dell'IS (WR non sotto
50%); DD OOS ≤ DD IS × 1.5; equity con drift. Fail → **cimitero**, non si torna indietro.

## Stage 6 — Bootstrap (Colab Monte Carlo, IS + OOS)
Export List of Trades → notebook. Risk per contract = SL medio in $.

**Gate 6**: EV > 0 in $ e in R; P(EV ≤ 0) < 5% IS, < 10% OOS; CI IS/OOS sovrapposti.
Salva percentili DD dopo 10/20/40 trade (yardstick live).

## Stage 7 — Simulatore prop, singola strategia (Colab prop, OOS)
Regole della prop inserite; sweep sui micro; correlazione fra tentativi.

**Gate 7 — EVAL**: pass rate 1° tentativo ≥ 40%; entro 4 tentativi ≥ 85%; giorni medi
per passare ≤ 15; DD medio < limite; size ottimale ≤ size "affidabile" (95° perc.
perdita/contratto).
**Gate 7 — FUNDED**: qualification rate ≥ 50% alla size di sopravvivenza; expected
payout > costo del budget (≥ 4 × fee).

## Stage 8 — Basket
Tutte le strategie che hanno passato lo Stage 7 vanno nel simulatore multi‑strategia.

**Gate 8**: correlazione a coppie ≤ 0.2 (meglio ≤ 0); giorni attivi ≥ 90%; pass rate del
basket > migliore singola; qualification funded ≥ 70%; nessuna strategia in drawdown
oltre il 75° perc. al momento del deploy (quelle in DD pesante si benchano).
Size per strategia = output del simulatore (micro), cap totale ≤ 2 mini.

## Stage 9 — Deploy
Paper ≥ 1 settimana; poi eval con size del simulatore, **budget dichiarato** (es. 3
tentativi), stessa strategia a ogni tentativo. VPS se > 1 strategia. Monitoraggio: DD vs
percentili (75° riduci, 95° stop), avg trade live vs backtest a 3 mesi. Piccole
randomizzazioni per non essere identici agli altri account.

---

## Stato

| Strategia | Famiglia | Stage | Note |
|---|---|---|---|
| ORB_Breakout (NQ 5m) | trend | **1 ✔ → 2 bloccato** | serve storico ≥ 5 anni (dati free = 4 mesi) |
| VaultBreak (NQ 5m) | trend | 0 | template del corso, da spec |
| VWAP‑ADX (NQ 1m) | mean rev | 0 | template Agnello, da spec |
| Gold Asian Range (GC 15m) | trend, altro asset | 0 | winner Strategy of the Month |
| Evento macro (CPI/FOMC) | evento | — | dopo i primi tre |

**Blocco attuale**: lo storico. Con 4 mesi non si supera nessun gate dal 2 in poi.
Decisione da prendere: TradeStation (deposito $500 → dati gratis 6 mesi) o IQFeed.
