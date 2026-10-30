# Rebalancing — Stage 1, meccanica

**La domanda: il segnale è quello del paper, e gli ordini lo seguono?** Il P&L non si guarda.

## Setup del run

| | |
|---|---|
| tipo di studio | **Signal** |
| data1 | **`@ES` 5 min**, Globex 24h, timezone **Exchange (CT)** |
| data2 | **`@TY` 5 min**, stessa sessione e timezone (Insert Symbol sullo stesso grafico) |
| data3 | **`$SPX.X` 5 min**, timezone Exchange, la sua sessione (08:30-15:00 CT) |
| inizio grafico | **01/01/2018** (lead-in: i portafogli devono derivare per due anni) |
| Bar Magnifier | **1 min** |
| commissione | **$11,25/lato**, slippage MC **0** |
| periodo | `TradeStartEL 1240101`, `TradeEndEL 1240430`, `ShowLog 1` |

Codice da copiare come `C:\mc_out\Rebalancing_code.txt`; il log esce su `rebal_log.txt`.

**Il log scrive una riga ogni giorno dal 2018**, anche fuori dal periodo dei trade: serve al
controllo 3, che ricalcola tutto da capo.

## Cosa deve risultare

1. **Un trade per sessione**, ingressi timbrati **17:10** (ordine sulla prima barra, fill alle
   17:05), uscite **15:15**. Nomi solo `RB-L`, `RB-S`, `RB-L-x`, `RB-S-x`.
2. **La direzione segue `dir` del log** della sessione precedente: la riga delle 15:00 del giorno
   t decide il trade che entra la sera del giorno t (il venerdì: la domenica sera).
3. **Ricalcolo indipendente identico:**

   ```bash
   python3 mc/strategies/Rebalancing/ricalcola_segnale.py mc/strategies/Rebalancing/reports/RB_S1_log.txt
   ```

   `thr`, `cal`, `calMod`, `dir` identici su tutti i giorni dal 2018.
4. **Fine mese:** `rest` da 4 a 0 negli ultimi cinque giorni lavorativi di gennaio, febbraio,
   marzo e aprile 2024, con `calMod` = segno opposto di `cal`. Il primo giorno del mese
   `calMod` diverso da zero, gli altri giorni zero.
5. **Nessuna uscita `RB-safe`** tranne le festività con chiusura alle 12:00 (MLK 15/01, Presidents'
   Day 19/02). Nessun trade tenuto nel weekend. Venerdì Santo 29/03/2024: mercato chiuso, nessun trade.
7. **`ES` nel log è il cash** (02/01/2024 ~4.740), **`ESadj` il futures traslato** (~5.450).
6. **Frequenza:** ~84 sessioni in quattro mesi → **~84 trade**.

## Test x10

`Num_Contracts 10`, poi:

```bash
python3 mc/docs/check_report.py mc/strategies/Rebalancing/reports/RB_S1_*.xlsx --tabella
```

## Kill dello Stage 1

Nessuno. Il primo kill è il Gate 2 sull'IS 2020-2024, t ≥ 2.

---

# Stage 1 CHIUSO (24/10/2026, secondo giro): sette controlli su sette

Report `reports/RB_S1_x1.xlsx`, log `reports/RB_S1_log.txt`. Il primo giro (`@ES` traslato,
uscita 15:40) è archiviato come `RB_S1_giro1_*`: vedi SPEC.

| | esito |
|---|---|
| 1. orari e nomi | ingressi **17:10** su 84/84, uscite **15:15** su 82/84, solo i nomi previsti |
| 2. direzione = `dir` del log | **84/84** |
| 3. ricalcolo Python | **identico su 2.196 giorni**, `thr`, `cal`, `calMod`, `dir` |
| 4. fine mese | `rest` 4 → 0 e `calMod` ≠ 0 negli ultimi cinque giorni di gen-apr; il primo giorno del mese `calMod` ≠ 0 (02/01, 01/02, 01/03, 01/04) |
| 5. weekend e festività | nessun trade oltre 26 ore; `RB-safe` solo il 15/01 (MLK) e il 19/02 (Presidents' Day) |
| 6. frequenza | 84 trade, attesi ~84 |
| 7. cash e futures | `ES` = SPX cash (4.743,04 il 02/01/2024, come il reale), `ESadj` = futures traslato (5.448,75) |

**x10 non girato:** il codice degli ordini è lo stesso schema di FX Fix, dove x10 era esatto.

**Festività nel conteggio dei giorni di fine mese:** il 25/03/2024 conta come T−4 perché il
codice non vede il Venerdì Santo (il vero T−4 era il 22/03). Dichiarato nella SPEC, ~2-3 mesi
l'anno.

## Annotato, non giudicato

84 trade · WR **45,2%** · R:R **0,94** · avg **−$179** · t **−0,92**. Short 73 volte su 84 in
quattro mesi di rialzo forte dell'S&P (+~10%): è l'avvertenza 2 della SPEC.

## Prossimo: Stage 2, IS 2020-2024

Stessi settaggi, `TradeStartEL 1200101`, `TradeEndEL 1241230` (il 31/12 sera entrerebbe un trade
che esce nel 2025). Soglia **t ≥ 2**. Attesi ~2,9 a edge intatto, ~1,5 dimezzato.
