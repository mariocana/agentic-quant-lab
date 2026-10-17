# CHECKLIST Stage 1 — BTC First30 Short

Chart: `@BTC` · 5 min · Bar Magnifier 1 min · commissione **$175 per contratto** (50 MBT ×
$3,50, slippage ripiegata dentro, campo slippage 0) · Point Value $5 · sessione Globex 24h
(ultima barra 16:00). Periodo: **2026‑06‑24 → 2026‑10‑16** (114 giorni, 37 trade).

| run | `StopMode` | `TP_RR` | `Num_Contracts` | file | stato |
|---|---|---|---|---|---|
| A | 0 | 0 | 1 | `reports/B30_S1_A_nostop_x1.xlsx` | valido |
| B | 0 | 0 | 10 | `reports/B30_S1_B_nostop_x10.xlsx` | valido |
| C | 1 | 0 | 1 | — | **da rifare** (difetto del bracket) |
| D | 1 | 1 | 1 | — | **da rifare** (difetto del bracket) |

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

## Per il secondo giro
1. Ricompila `BTC_First30.txt` (versione con `SetStopLoss` / `SetProfitTarget`).
2. Rifai **C** e **D** sullo stesso periodo, con `ShowLog 1` almeno su C, e salva il log.
3. Controlli da chiudere: 1, 2, 6, 7 (distribuzione completa di `rischio_pt` su tutti i
   giorni, non solo quelli a stop) e 9. In D nessun `Profit Target` deve essere riempito
   oltre il suo prezzo.
