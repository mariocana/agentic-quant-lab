# Rebalancing — Stage 1, meccanica

**La domanda: il segnale è quello del paper, e gli ordini lo seguono?** Il P&L non si guarda.

## Setup del run

| | |
|---|---|
| tipo di studio | **Signal** |
| data1 | **`@ES` 5 min**, Globex 24h, timezone **Exchange (CT)** |
| data2 | **`@TY` 5 min**, stessa sessione e timezone (Insert Symbol sullo stesso grafico) |
| inizio grafico | **01/01/2018** (lead-in: i portafogli devono derivare per due anni) |
| Bar Magnifier | **1 min** |
| commissione | **$11,25/lato**, slippage MC **0** |
| periodo | `TradeStartEL 1240101`, `TradeEndEL 1240430`, `ShowLog 1` |

Codice da copiare come `C:\mc_out\Rebalancing_code.txt`; il log esce su `rebal_log.txt`.

**Il log scrive una riga ogni giorno dal 2018**, anche fuori dal periodo dei trade: serve al
controllo 3, che ricalcola tutto da capo.

## Cosa deve risultare

1. **Un trade per sessione**, ingressi timbrati **17:10** (ordine sulla prima barra, fill alle
   17:05), uscite **15:45**. Nomi solo `RB-L`, `RB-S`, `RB-L-x`, `RB-S-x`.
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
5. **Venerdì Santo 29/03/2024** (mercato chiuso): nessun trade quella sera, e nessuna uscita
   `RB-safe` lasciata in giro.
6. **Frequenza:** ~84 sessioni in quattro mesi → **~84 trade**.

## Test x10

`Num_Contracts 10`, poi:

```bash
python3 mc/docs/check_report.py mc/strategies/Rebalancing/reports/RB_S1_*.xlsx --tabella
```

## Kill dello Stage 1

Nessuno. Il primo kill è il Gate 2 sull'IS 2020-2024, t ≥ 2.
