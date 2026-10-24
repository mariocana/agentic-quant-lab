# Trend Following di Unger (6E, GC, ES, NQ) — istruzioni

Codici: **`UngerTF_A.txt`** → salva come `Mario_UngerTF_A`, **`UngerTF_B.txt`** →
`Mario_UngerTF_B` (signal). Richiedono la funzione **`Mario_PtnBaseSA`**. Spec: `SPEC.md`.
`UngerTF.txt` e `UngerTF_ID.txt` sono le trascrizioni fedeli dal video (forex), non da usare.

## Chart
- **15 min**, data source TradeStation, timezone **Exchange**, Bar Magnifier **1 min ON**,
  Backtesting Mode Classic, Max bars back 50.
- **@EC, @ES, @NQ**: exchange Chicago, template **"CME Globex 17-16 no break"**.
- **@GC**: exchange New York, template **"COMEX Globex 18-17 no break"**.
- Costi per contratto, slippage `0 ticks`: @EC `8.65$`, @GC `12.5$`, @ES `15$`, @NQ `7.5$`.

## Input per strumento (tutto il resto ai default)

| | A: `MyStartTrade` / `MyEndTrade` | A: stop / target | B: `MyStartTrade` / `MyEndTrade` | B: stop / target |
|---|---|---|---|---|
| @EC | 300 / 1230 (default) | default (`StopPts 0.011`, `ProfitPts 0.035`) | 200 / 400 (default) | default (`StopPts 0.0075`, `ProfitPts 0.025`) |
| @GC | **400 / 1330** | `StopPct 0.83`, `ProfitPct 2.6`, `StopPts 0`, `ProfitPts 0` | **300 / 500** | `StopPct 0.56`, `ProfitPct 1.9`, `StopPts 0`, `ProfitPts 0` |
| @ES, @NQ | default | come GC | default | come GC |

Controlla gli input in *Format Signals* prima di ogni run: ricompilare non aggiorna quelli di
una strategia già sul grafico.

## Stage 1 — meccanica, ~100 giorni

| run | chart | size | file in `reports/` |
|---|---|---|---|
| A | @EC | 1 | `TF_S1_EC_A_x1.xlsx` + log (`ShowLog 1`) |
| A10 | @EC | 10 | `TF_S1_EC_A_x10.xlsx` |
| B | @EC | 1 | `TF_S1_EC_B_x1.xlsx` + log |
| B | @GC (input di GC) | 1 | `TF_S1_GC_B_x1.xlsx` + log |

### Controlli (Gate 1)
1. **Finestra**: in A gli ingressi cadono fra le 03:15 e le 12:30 CT (GC: un'ora dopo, NY), in
   B fra le 02:15 e le 04:00 CT (GC 03:15–05:00 NY). Mai di domenica.
2. **Livelli**: `entry` = `hiD` (long) o `loD` (short) del momento, o peggio se il prezzo salta.
3. **Filtri**: in A nessun ingresso dopo un giorno con corpo ≥ 50% del range; in B nessun
   ingresso con la giornata ancora inside rispetto a ieri (li ricontrollo io con i dati).
4. **Stop / target**: @EC A $1.375 / $4.375, B $937,50 / $3.125 a contratto; GC in % del
   prezzo d'entrata (`stop$` e `tgt$` nel log).
5. **Uscite**: A tiene anche overnight e si gira sul segnale opposto; B è flat a fine sessione
   (16:00 CT, 17:00 NY su GC).
6. **Scala ×10**: A10 = 10 × A.

## Stage 2 — IS 2020‑01‑01 → 2024‑12‑31, 1 contratto, senza log
A e B su @EC, @GC, @ES, @NQ: 8 run, file `TF_S2_<EC|GC|ES|NQ>_<A|B>_IS.xlsx`.
Mandami lo Stage 1 prima.
