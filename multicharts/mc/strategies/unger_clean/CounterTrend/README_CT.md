# Counter Trend di Unger (GC; ES e YM esplorativi) — istruzioni

Codice: `Mario_UngerCT.txt` (signal). Richiede la funzione **`Mario_PtnBaseSA`** già compilata.
Spec: `SPEC.md`.

## Chart (uguale per i tre strumenti)
- **@GC** (poi @ES, @YM) · **30 min**, data source TradeStation, timezone **Exchange** (CT).
- Session template **17:00–16:00 CT senza pause** (quello personalizzato di ESCounter). Su GC
  **non** il template `COMEX: Metals Futures (Electronic)`.
- Bar Magnifier **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- Costi per contratto, slippage `0 ticks`: **GC `12.5$`**, ES `15$`, YM `7.5$`.
- Input ai default (Unger + `MyStartTime 200`, `StopPct 0.65`).

## Stage 1 — meccanica, solo su GC (~100 giorni)

| run | `FlatEOD` | size | file in `reports/` |
|---|---|---|---|
| A | 0 | 1 | `CT_S1_GC_A_x1.xlsx` + log (`ShowLog 1`) |
| A10 | 0 | 10 | `CT_S1_GC_A_x10.xlsx` |
| B | 1 | 1 | `CT_S1_GC_B_x1.xlsx` |

### Controlli (Gate 1)
1. **Finestra**: i segnali `CT S` / `CT L` del log cadono fra le **02:30 e le 05:00 CT**
   (`cnt` da 2 a 7), mai di domenica.
2. **Filtri**: long solo dopo un giorno chiuso in rialzo, short dopo uno in ribasso, mai dopo
   un outside bar (li ricontrollo con i valori di sessione).
3. **Stop**: ogni `Stop Loss` è a **0,65% del close del segnale** (`stop$` nel log, ~$2.670 su
   un GC a 4.100), né prima né oltre.
4. **Inversioni**: un segnale opposto gira la posizione.
5. **Variante B**: flat alle 16:00 CT, nessuna posizione overnight.
6. **Scala ×10**: A10 = 10 × A.
7. **Back‑adjustment**: guarda sul chart il close di @GC al 02/01/2020 e annotalo; il prezzo
   reale dell'oro quel giorno era intorno a 1.525.

## Stage 2 — IS 2020‑01‑01 → 2024‑12‑31, 1 contratto, senza log
- **GC**: run **A** e **B**.
- **ES** e **YM** (esplorativi): run **A** e **B** ciascuno, con i loro costi.

Mandami Stage 1 prima dello Stage 2: se la meccanica ha un difetto, i sei run dell'IS sarebbero
da rifare.
