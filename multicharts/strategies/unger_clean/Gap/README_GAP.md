# GoldGapper di Unger — istruzioni Stage 1

Codice: `GoldGapper.txt` (signal). Spec: `SPEC.md`.

## Prima di tutto: le funzioni del corso
In MultiCharts: **File → Import** (o PowerLanguage Editor → File → Import) del file
`education/unger/Trading System Supremacy/13. Codici/Gap/GapsFunctions/GapsFunctions.pla`.
Porta tre funzioni: `_DayDefinition`, `Time00`, `TradesToday`. **Non** creare
`_DayDefinition` incollando il `.txt`: è una versione modificata con cui la strategia non fa
trade. Se le tre funzioni esistono già nel tuo MultiCharts, sovrascrivile con quelle del
`.pla`. Poi compila `Mario_GoldGapper`.

## Chart
- **@GC · 5 min**, data source TradeStation, timezone **Exchange**: per @GC è l'ora di **New
  York** (il COMEX), non Chicago come per @ES.
- Session template **nuovo per l'oro**: domenica–venerdì **18:00 → 17:00**, Session Time
  *Exchange*, senza pause (es. "COMEX Globex 18-17 no break"). **Non** il "CME Globex 17-16 no
  break" di ES: su @GC vale 17:00–16:00 di New York, taglia l'ultima ora dell'oro e non ha
  la barra delle 18:00.
- Bar Magnifier **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- Costi **`12.5$ per Contract`**, slippage **`0 ticks`**.
- Periodo: ultimi **~100 giorni** (pochi trade attesi: se ne escono meno di 5, allunga a 200).

## Run dello Stage 1

**Controlla gli input sul chart.** Ricompilare cambia i default solo per le strategie inserite
dopo: quella già sul grafico tiene i valori di prima. Apri *Format Signals → Inputs* e verifica
`sBeg 2005`, `sEnd 1900` (o `1600` per B). Il giro del 24/10 è stato invalidato proprio da
questo (`sBeg 1905`, `sEnd 1800` rimasti dal codice vecchio).

| run | input | size | file in `reports/` |
|---|---|---|---|
| A | default (`sBeg 2005`, `sEnd 1900`) + `ShowLog 1` | 1 | `GG_S1_A_x1.xlsx` + log |
| A10 | come A | 10 | `GG_S1_A_x10.xlsx` |
| B | `sEnd 1600` | 1 | `GG_S1_B_x1.xlsx` |

## Verifica meccanica (Gate 1)
1. **Giornata giusta**: ogni riga `GAP DAY` è alle **20:05**. `hi_ieri` / `lo_ieri` = massimo e
   minimo da 20:05 del giorno prima alle 19:00 (controllane due a mano sul chart). Se
   `hi_ieri` è uguale al massimo della barra delle 20:05, la funzione è quella sbagliata (il
   `.txt`).
2. **Ingressi solo nei giorni di gap**: trade solo dopo righe con `gap= 1` (short) o `gap=-1`
   (long), al prezzo `hi_ieri` (short) o `lo_ieri` (long), o peggio se il prezzo salta il livello.
3. **Un ingresso per data**, al massimo due per giornata personalizzata (prima e dopo mezzanotte).
4. **Stop**: le uscite `Stop Loss` sono a **20 punti** dall'entrata ($2.000 + costi).
5. **Uscita a tempo**: A esce dopo la barra delle **19:00**, B dopo quella delle **16:00** (ora di
   New York); in B nessuna posizione oltre le 17:00.
6. **Scala ×10**: A10 = 10 × A.

Mandami i tre `.xlsx` e il log del run A.

## Stage 1 — **passato** (24/10/2026, terzo giro)
Con `sBeg 2005` le righe `GAP DAY` sono alle 20:05. Controllati trade per trade:
- 9 giorni di gap nel log del run A (7/6, 9/6, 18/6, 5/8, 9/8, 10/8, 16/8, 18/10, 19/10);
  ingresso in 6, negli altri 3 il prezzo non è mai tornato sul bordo (es. 9/6: minimo di ieri
  4.315,30, il giorno dopo il prezzo resta sotto, a 4.130);
- ingressi a `hi_ieri` / `lo_ieri`, o peggio quando il prezzo salta il livello (9/8 buy stop
  a 4.392,10 eseguito a 4.400,60);
- secondo ingresso dopo mezzanotte allo stesso livello dopo uno stop (5–6/8, 9–10/8, 19–20/10);
- stop a 20 punti, uscita a tempo alle 19:05 in A e alle 16:05 in B, nessuna posizione di B
  oltre le 17:00.

Run A: 10 trade, WR 60%, avg +$1.364; run B: 12 trade, WR 33%, avg +$809. Su così pochi trade
non dicono niente sull'edge.

## Stage 2 — IS 2020‑01‑01 → 2024‑12‑31, 1 contratto, senza log
Stesso chart (@GC 5 min, template 18-17, Bar Magnifier 1 min, costi 12.5$):

| run | input | file in `reports/` |
|---|---|---|
| A | `sBeg 2005`, `sEnd 1900` | `GG_S2_A_IS.xlsx` |
| B | `sBeg 2005`, `sEnd 1600` | `GG_S2_B_IS.xlsx` |

`ShowLog 0`. Prima di lanciare, controlla gli input in *Format Signals*.
