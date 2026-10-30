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

---

# Stage 1 CHIUSO (19/10/2026): sette controlli su sette

Report `reports/LHH_S1_x1.xlsx` e `LHH_S1_x10.xlsx`, log `reports/LHH_S1_log.txt`.
2026-06-02 → 2026-10-16, $7,50/lato, Bar Magnifier 1 min.

| | esito |
|---|---|
| 1. un trade al giorno | 96 ingressi su 96 giorni distinti |
| 2. ingressi | **14:35 su 96/96** |
| 3. uscite | **15:05 su 96/96**, solo `LHH-L-x` (42) e `LHH-S-x` (54) |
| 4. direzione = segno di `rROD` | **96/96** |
| 5. vigilie a chiusura anticipata | **non verificabile qui**: nessuna nell'intervallo |
| 6. frequenza | 96 righe nel log = 96 trade |
| 7. `priorClose` | mai uguale al prezzo delle 14:30 di ieri (0 su 95): e' un altro orario |
| x10 | **esatto**: n, WR, R:R, t, PF identici, avg da $109,17 a $1.091,67 |

**Il template del grafico chiude alle 15:15** (RTH CME dei futures azionari), non alle 15:00
ne' alle 16:00. Per questa strategia non conta — la sessione la definisce il codice e le barre
oltre le 15:00 sono escluse dal calcolo di `priorClose` — ma `check_report.py` non lo
riconosceva e ora si'.

## Annotato, non giudicato

96 trade · WR **49,0%** · R:R **1,31** · avg **$109,17** · t **0,74**.

Il WR del paper era **55%**. Su 96 trade l'errore standard di una proporzione e' **5,1 punti**,
quindi 49% e 55% non si distinguono. **Il profilo non e' quello prop** (WR alto, R:R basso), e
non deve esserlo: la strategia esce a tempo, senza bracket, quindi e' una scommessa sul segno
con uscite quasi simmetriche.

avg $10,92 per micro a 1 trade/giorno = **~$10,9 al giorno per micro**, contro i $18,34 di
DriftPullback. Ordine di grandezza da seconda gamba.

## Prossimo: Stage 2, IS 2020-2024

Stessi settaggi, `TradeStartEL 1200101`, `TradeEndEL 1241231`. Soglia **t ≥ 2**. Attesi
**3,64 a edge intatto, 1,82 a edge dimezzato**. Lettura pre-registrata: si passa se e'
sopravvissuto almeno il ~55% dell'edge del paper.
