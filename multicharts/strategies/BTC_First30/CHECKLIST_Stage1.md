# CHECKLIST Stage 1 — BTC First30 Short — **Gate 1 passato** (17/10/2026, secondo giro)

Chart: `@BTC` · 5 min · Bar Magnifier 1 min · commissione **$175 per contratto** (50 MBT ×
$3,50, slippage ripiegata dentro, campo slippage 0) · Point Value $5 · sessione Globex 24h
(ultima barra 16:00). Periodo: **2026‑06‑24 → 2026‑10‑16** (114 giorni, 37 trade).

| run | `StopMode` | `TP_RR` | `Num_Contracts` | file | stato |
|---|---|---|---|---|---|
| A | 0 | 0 | 1 | `reports/B30_S1_A_nostop_x1.xlsx` | valido |
| B | 0 | 0 | 10 | `reports/B30_S1_B_nostop_x10.xlsx` | valido |
| C | 1 | 0 | 1 | `reports/B30_S1_C_orstop_x1.xlsx` + `B30_S1_C_log.txt` | valido (secondo giro) |
| D | 1 | 1 | 1 | `reports/B30_S1_D_orstop_tp1_x1.xlsx` | valido (secondo giro) |

---

## Primo giro (17/10/2026) — **Gate 1 non passato**: difetto nel codice

### Il difetto: la barra d'ingresso restava senza stop e senza target

Stop e target venivano emessi come ordini `next bar` sulla barra **dopo** l'ingresso. La
barra 09:00–09:05, quella in cui la posizione entra, restava scoperta.

Il caso che l'ha mostrato, **14/07/2026**, short a 65.055:

| run | uscita | prezzo | distanza dall'entry |
|---|---|---|---|
| C (stop) | `S-SL` alle 09:35 | 65.200 | **+145 pt** = rischio del giorno |
| D (TP 1R) | `S-TP` alle 09:10 | 64.825 | **−230 pt**, invece di −145 |

Con TP = 1R il target doveva essere a 64.910. Il prezzo ci è sceso già nei primi 5 minuti
(run‑up $1.300 = 260 pt), quando l'ordine non esisteva ancora. È stato emesso alle 09:05 e
riempito all'apertura dopo, **85 pt meglio del suo prezzo**. Lo stesso buco vale per lo
stop, nel verso peggiore: uno stop superato nei primi 5 minuti non scatta, e la perdita
risulta più piccola del vero.

**Correzione** (codice aggiornato lo stesso giorno): stop e target diventano ordini speciali
`SetStopLoss` / `SetProfitTarget`, attivi dalla barra d'ingresso, come in VaultBreak.
Importo per posizione × `Num_Contracts`, non `CurrentContracts` (lezione di NQ_First5). Lo
stop ora è a entry + (massimo della finestra − close delle 09:00): coincide con il massimo a
meno dello scarto fra close e open delle 09:00. Nella List of Trades le uscite si chiamano
`Stop Loss` e `Profit Target`.

Il difetto c'è anche in **GoldAsianRange**, che usa lo stesso schema (bracket `next bar`
dopo l'ingresso). Lì gli ingressi sono ordini stop, quindi la barra scoperta è quella in cui
scatta il breakout: va controllato.

### Controlli fatti sulla List of Trades

| # | controllo | esito |
|---|---|---|
| 3 | entrate alle **09:05**, uscite a tempo alle **15:05** | ✅ 37/37 entrate alle 09:05; uscite a tempo alle 15:05, una alle 15:10 (vedi 10) |
| 4 | solo lunedì–venerdì | ✅ nessun trade nel weekend (Lun 7, Mar 9, Mer 9, Gio 5, Ven 7) |
| 5 | un trade al giorno, zero overnight | ✅ nessun giorno con due trade, 0 overnight |
| 8 | run B = 10 × run A | ✅ P&L identico ×10 su tutti i 37 trade |
| — | P&L ricalcolato = (entry − exit) × $5 − 2 × $175 | ✅ su tutti i trade di A, C, D |
| 7 | guardrail `MaxRiskPts 4000` | non è mai scattato: A e C hanno gli stessi 37 ingressi. Le distanze di stop dei 23 trade chiusi a stop in C vanno da **135 a 820 pt** (mediana ~380 pt = **$38 per MBT**), ben sotto 4.000 |
| 10 | festività USA | **07/09/2026, Labor Day**: un trade, uscito alle 15:10 perché manca la barra delle 15:00. Il 03/07 (festivo osservato) nessun trade. Da annotare, non si toglie ora |
| 1, 2 | finestra di 6 barre; entrata solo con `delta` < 0 | **non verificabili**: manca il log |
| 6, 9 | stop e target al prezzo giusto | **falliti**: è il difetto sopra |

### Numeri (informativi: lo Stage 1 giudica la meccanica, non il risultato)

| run | n | WR | avg trade | PF | net |
|---|---|---|---|---|---|
| A (senza stop) | 37 | 37,8% | −$1.183 (t −1,47) | 0,49 | −$43.775 |
| C (stop) | 37 | 27,0% | −$595 | 0,63 | −$22.000 |
| D (stop + TP 1R) | 37 | 45,9% | −$393 | 0,71 | −$14.525 |

In MBT (÷50) il run A è −$875 in quattro mesi. Con 37 trade la t è −1,47: è perdente, ma
non abbastanza da dire qualcosa. C e D sono falsati dal difetto, e in D il difetto rende i
numeri **migliori** del vero. Questo periodo cade nell'OOS (2025 →): come per GAR, i run
dello Stage 1 servono solo alla meccanica e non entrano in nessuna decisione.

---

## Secondo giro (17/10/2026) — codice con `SetStopLoss` / `SetProfitTarget`, **Gate 1 passato**

C e D rifatti sullo stesso periodo; log del run C in `reports/B30_S1_C_log.txt`. Ogni
controllo incrocia la List of Trades con il log, giorno per giorno.

| # | controllo | esito |
|---|---|---|
| 1 | finestra giusta | ✅ tutti gli 84 giorni feriali: `t= 900`, `barre= 6`, `completa=TRUE` |
| 2 | entrata solo nei giorni negativi | ✅ `short=TRUE` se e solo se `delta` < 0, su tutti gli 84 giorni (37 short, 44%) |
| 3 | orari | ✅ entrate alle 09:05; uscite a tempo alle 15:05 (una alle 15:10, Labor Day) |
| 4 | solo lunedì–venerdì | ✅ nessun trade nel weekend. Il log ha 16 righe di domenica (`t=` 16:05–16:25, `barre= 0`, `completa=FALSE`): è la riapertura della domenica sera, scartata come previsto. Rumore nel log, non nei trade |
| 5 | un trade al giorno, zero overnight | ✅ |
| 6 | stop | ✅ `SL` = entry + `rischio_pt` su tutti i 37 ingressi. Le 23 uscite `Stop Loss` di C sono **esattamente** al prezzo di stop, nessuna oltre. L'ingresso alle 09:00 differisce dal close delle 09:00 di 0 pt in mediana (da −115 a +100), quindi lo stop sta di fatto sul massimo della finestra |
| 7 | guardrail e distribuzione del rischio | ✅ `MaxRiskPts 4000` mai superato. `rischio_pt` sui 37 ingressi: min 150, **mediana 430**, 90° perc. 705, **max 3.130** (25/06, finestra −3.020 pt). Per MBT: mediana **$43**, 90° perc. $71, max **$313**, sotto i $400 del worst day di spec |
| 8 | scala ×10 | ✅ (primo giro) |
| 9 | target 1R (D) | ✅ i 17 `Profit Target` sono **esattamente** a entry − `rischio_pt`. Tre sono presi dentro la barra d'ingresso (14/07, 25/09, 29/09): è proprio il caso che il primo giro sbagliava. Il 14/07 ora esce a 64.905 (1R = 150 pt), non a 64.825 |
| 10 | festività USA | 03/07 (Independence Day osservato): finestra regolare, `delta` +65, nessun trade. 07/09 (Labor Day): un trade, uscita alle 15:10 perché manca la barra delle 15:00. Annotati: si decide allo Stage 2 se escluderli |

### Numeri del secondo giro (informativi)

| run | n | WR | avg trade | per MBT | PF | net |
|---|---|---|---|---|---|---|
| A (senza stop) | 37 | 37,8% | −$1.183 | −$23,7 | 0,49 | −$43.775 |
| C (stop) | 37 | 27,0% | −$621 | −$12,4 | 0,62 | −$22.975 |
| D (stop + TP 1R) | 37 | 45,9% | −$486 | −$9,7 | 0,65 | −$17.975 |

Tutte e tre perdono, con t intorno a −1,2/−1,5: non significativo su 37 trade, e il periodo
è OOS, quindi non entra in nessuna decisione. Una nota però va scritta adesso: l'autore ha
pubblicato a settembre 2026 un PF di 1,91, e il suo periodo con ogni probabilità comprende
questi mesi. Qui, sugli stessi mesi, PF 0,49. O il suo periodo e il suo contratto sono
diversi, o il risultato dichiarato non si riproduce. Lo dirà l'IS.

## Verso lo Stage 2
- Prima: controllare @BTC a gennaio 2020 (prezzi positivi e plausibili, README).
- Run IS 2020‑01‑01 → 2024‑12‑31 con `ShowLog 1` (serve il rischio di ogni trade per la
  tabella annuale in R): **C** (stop), **D** (stop + TP 1R), **A** (senza stop, benchmark)
  e il **controllo long** (`TradeLongs 1`, `TradeShorts 0`, `StopMode 1`).
- Gate 2 con le soglie ÷50 della spec, non quelle di NQ di `check_report.py`.
