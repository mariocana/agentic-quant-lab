# Counter Trend di Unger (6B) — istruzioni Stage 1

Codice: `Mario_UngerCT.txt` (signal). Richiede la funzione **`Mario_PtnBaseSA`** già compilata.
Spec: `SPEC.md`.

## Chart
- **@BP (6B) · 30 min**, data source TradeStation, timezone **Exchange** (CT).
- Session template **CME Globex 17:00–16:00 CT senza pause** (quello personalizzato di ESCounter).
- Bar Magnifier **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- Costi: **`8.75$ per Contract`**, slippage **`0 ticks`**. Point Value 6B = $62.500 (tick
  0,0001 = $6,25): controllalo in QuoteManager.
- Periodo: ultimi **~100 giorni**.

## Run

| run | `FlatEOD` | size | file in `reports/` |
|---|---|---|---|
| A | 0 | 1 | `CT_S1_A_orig_x1.xlsx` + log (`ShowLog 1`) |
| A10 | 0 | 10 | `CT_S1_A_orig_x10.xlsx` |
| B | 1 | 1 | `CT_S1_B_eod_x1.xlsx` |

Input ai default (quelli finali di Unger, con `MyStartTime 200`).

## Verifica meccanica (Gate 1)
1. **Finestra**: i segnali `CT S` / `CT L` del log cadono fra le **02:30 e le 05:00 CT**
   (barre con `cnt` da 2 a 7), mai di domenica.
2. **Incrocio**: per ogni `CT S` il close è sotto `up` e la barra prima era sopra; per `CT L`
   il close è sopra `lo` e la barra prima sotto. Lo verifico dalla List of Trades.
3. **Filtri**: i long solo dopo un giorno chiuso in rialzo, gli short dopo un giorno in
   ribasso, mai dopo un outside bar. Lo verifico incrociando con i valori di sessione.
4. **Stop**: le uscite `Stop Loss` sono a **100 pip** dall'entrata ($625 + costi).
5. **Inversioni**: con posizione aperta, un segnale opposto la gira (nella List of Trades
   l'uscita ha il nome dell'ingresso opposto).
6. **Variante B**: flat alle 16:00 CT; nessuna posizione overnight.
7. **Scala ×10**: A10 = 10 × A.

Mandami i tre `.xlsx` e il log del run A.
