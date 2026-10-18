# Last Half-Hour — Stage 1, meccanica

**La domanda: il codice fa quello che dice il paper?** Il P&L non si guarda.

## Setup del run

| | |
|---|---|
| tipo di studio | **Signal**, non Indicator — contiene ordini |
| strumento | **@NQ, 5 min**, Globex 24h, timezone **Exchange (CT)** |
| Bar Magnifier | **1 min** (qui non conta: solo ordini a mercato, ma teniamo la convenzione) |
| contratti | **1** |
| commissione | **$7,50/lato**, slippage MC **0** |
| periodo | **100 giorni** recenti, `ShowLog 1` |
| input | tutti ai default |

Non serve lead-in: la strategia non ha medie da riempire, le basta la chiusura di ieri.

## Cosa deve risultare

1. **Al massimo un trade al giorno.**
2. **Tutti gli ingressi timbrati 14:35** (fill all'apertura delle 14:30).
3. **Tutte le uscite timbrate 15:05** (fill alle 15:00), coi nomi `LHH-L-x` e `LHH-S-x`. Se
   compare un altro nome, c'e' un ordine che non ho previsto.
4. **La direzione segue il segno di `rROD` nel log al 100%**: positivo → long, negativo o zero
   → short.
5. **Nessun trade nei giorni a chiusura anticipata** (vigilie di festa).
6. **Un trade per ogni giorno di sessione piena**, quindi circa **70 su 100 giorni di
   calendario**.
7. **`priorClose` nel log e' la chiusura delle 15:00 del giorno prima** — controllarne un paio
   a mano sul grafico. E' il pezzo su cui ON_Reversal aveva un difetto, quindi qui va guardato.

## Test x10

Rigirare con `Num_Contracts 10` e:

```bash
python3 mc/docs/check_report.py mc/strategies/LastHalfHour/reports/*_S1_*.xlsx --tabella
```

`n`, `WR%`, `R:R` identici, `avg` a x10.

## Kill dello Stage 1

Nessuno. Se la meccanica sbaglia si corregge il codice. Il primo kill e' il Gate 2 sull'IS
2020-2024, con t atteso **3,64** a edge intatto e **1,82** a edge dimezzato.
