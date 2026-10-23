# GoldGapper di Unger — istruzioni Stage 1

Codice: `Mario_GoldGapper.txt` (signal). Spec: `SPEC.md`.

## Prima di tutto: le funzioni del corso
In MultiCharts: **File → Import** (o PowerLanguage Editor → File → Import) del file
`education/unger/Trading System Supremacy/13. Codici/Gap/GapsFunctions/GapsFunctions.pla`.
Porta tre funzioni: `_DayDefinition`, `Time00`, `TradesToday`. **Non** creare
`_DayDefinition` incollando il `.txt`: è una versione modificata con cui la strategia non fa
trade. Se le tre funzioni esistono già nel tuo MultiCharts, sovrascrivile con quelle del
`.pla`. Poi compila `Mario_GoldGapper`.

## Chart
- **@GC · 5 min**, data source TradeStation, timezone **Exchange** (CT).
- Session template **17:00–16:00 CT senza pause** (quello personalizzato).
- Bar Magnifier **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- Costi **`12.5$ per Contract`**, slippage **`0 ticks`**.
- Periodo: ultimi **~100 giorni** (pochi trade attesi: se ne escono meno di 5, allunga a 200).

## Run dello Stage 1

| run | input | size | file in `reports/` |
|---|---|---|---|
| A | default (`sEnd 1800`) + `ShowLog 1` | 1 | `GG_S1_A_x1.xlsx` + log |
| A10 | come A | 10 | `GG_S1_A_x10.xlsx` |
| B | `sEnd 1500` | 1 | `GG_S1_B_x1.xlsx` |

## Verifica meccanica (Gate 1)
1. **Giornata giusta**: ogni riga `GAP DAY` è alle **19:05**. `hi_ieri` / `lo_ieri` = massimo e
   minimo da 19:05 del giorno prima alle 18:00 (controllane due a mano sul chart). Se
   `hi_ieri` è uguale al massimo della barra delle 19:05, la funzione è quella sbagliata (il
   `.txt`).
2. **Ingressi solo nei giorni di gap**: trade solo dopo righe con `gap= 1` (short) o `gap=-1`
   (long), al prezzo `hi_ieri` (short) o `lo_ieri` (long), o peggio se il prezzo salta il livello.
3. **Un ingresso per data**, al massimo due per giornata personalizzata (prima e dopo mezzanotte).
4. **Stop**: le uscite `Stop Loss` sono a **20 punti** dall'entrata ($2.000 + costi).
5. **Uscita a tempo**: A esce alle **18:00 CT** (barra `sEnd`), B alle **15:00 CT**; in B nessuna
   posizione oltre le 16:00.
6. **Scala ×10**: A10 = 10 × A.

Mandami i tre `.xlsx` e il log del run A.
