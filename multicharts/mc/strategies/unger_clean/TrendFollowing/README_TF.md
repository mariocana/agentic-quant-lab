# Trend Following di Unger (6E, GC, ES, NQ) — istruzioni

Codice unico: **`UngerTF.txt`** → salva come **`Mario_UngerTF`** (signal); input **`Versione`**
0 = A (multi‑day), 1 = B (intraday). Richiede la funzione **`Mario_PtnBaseSA`**. Spec: `SPEC.md`.

## Chart
- **15 min**, data source TradeStation, timezone **Exchange**, Bar Magnifier **1 min ON**,
  Backtesting Mode Classic, Max bars back 50.
- **@EC, @ES, @NQ**: exchange Chicago, template **"CME Globex 17-16 no break"**.
- **@GC**: exchange New York, template **"COMEX Globex 18-17 no break"**.
- Costi per contratto, slippage `0 ticks`: @EC `8.65$`, @GC `12.5$`, @ES `15$`, @NQ `7.5$`.

## Input per strumento
Gli input a 0 prendono il default della versione (orari di Chicago, stop e target di Unger in
prezzo). Si cambia solo questo:

| | A (`Versione 0`) | B (`Versione 1`) |
|---|---|---|
| @EC | niente | niente |
| @ES, @NQ | `StopPct 0.83`, `ProfitPct 2.6` | `StopPct 0.56`, `ProfitPct 1.9` |
| @GC | `MyStartTrade 400`, `MyEndTrade 1330`, `StopPct 0.83`, `ProfitPct 2.6` | `MyStartTrade 300`, `MyEndTrade 500`, `StopPct 0.56`, `ProfitPct 1.9` |

Controlla gli input in *Format Signals* prima di ogni run: ricompilare non aggiorna quelli di
una strategia già sul grafico.

## Stage 1 — meccanica, ~100 giorni

| run | chart | size | file in `reports/` | |
|---|---|---|---|---|
| A | @EC | 1 | `TF_S1_EC_A_x1.xlsx` + log (`ShowLog 1`) | ✅ 24/10 (con `Mario_UngerTF_A`, stessa logica) |
| A10 | @EC | 10 | `TF_S1_EC_A_x10.xlsx` | |
| B (`Versione 1`) | @EC | 1 | `TF_S1_EC_B_x1.xlsx` + log | |
| B (`Versione 1`) | @GC (input di GC) | 1 | `TF_S1_GC_B_x1.xlsx` + log | |

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

## Note dello Stage 1
**Run A su @EC (24/10/2026)**: 38 trade in 114 giorni, report `TF_S1_EC_A_x1.xlsx`, log
`TF_S1_EC_A_log.txt`.
- Ingressi fra le 03:30 e le 12:14 CT, in 21 giornate su ~80: dentro la finestra.
- Ingresso a `hiD` / `loD` del momento (il log stampa i valori a fine barra, quando il
  massimo può essere già salito oltre l'entrata).
- Stop $1.375 e target $4.375 a contratto, come da spec. In 114 giorni **non scatta né lo stop
  né il target**: tutte le uscite sono inversioni, perché il livello opposto (il minimo o il
  massimo del giorno) è quasi sempre più vicino di 110 pip. È la meccanica di Unger.
- **Inversioni a raffica nei giorni laterali**: il 28/08 sette trade in sei ore, con perdite
  da $110 a $225 ciascuno. Previsto dal codice (i due stop d'ingresso restano attivi tutta la
  finestra), ed è il costo principale della versione A.
- Il filtro del pattern 1 non si può ricontrollare qui (nessun dato di 6E in quantlake); la
  funzione `Mario_PtnBaseSA` è già verificata (Gate 1 del 18/10).

**Run B su @EC (24/10/2026) — invalido, e con lui il run A.** 20 trade, ingressi fra le 02:29
e le 03:59 CT (giusto), stop $937,50 / target $3.125 (giusto), un ingresso al giorno. Ma
l'uscita di fine sessione arriva alle **23:59**, e solo il venerdì alle 15:59: il chart di @EC
ha un template **a giorno di calendario** (00:00–23:59), probabilmente quello rimasto da FX Fix,
non il "CME Globex 17-16 no break". Conseguenze:
- in B la posizione resta aperta 8 ore oltre la chiusura delle 16:00, attraverso la pausa;
- in A e in B il massimo e il minimo "di oggi" partono da mezzanotte invece che dalle 17:00
  del giorno prima, e i pattern di "ieri" leggono il giorno di calendario.
Da rifare A e B su @EC con il template 17-16. Il run B è stato fatto con il vecchio
`Mario_UngerTF_B` (log `TFB`), con la stessa logica di `Versione 1`.

**Run B su @GC (24/10/2026) — meccanica giusta.** 19 trade in 130 giorni, report
`TF_S1_GC_B_x1.xlsx`, log `TF_S1_GC_B_log.txt` (tolte due righe di un primo giro con
`StopPts 0.56` al posto di `StopPct`).
- Ingressi fra le 03:30 e le 04:44 di New York, uno al giorno; dopo uno stop nessun rientro,
  perché la finestra è già chiusa.
- Stop allo **0,56% del prezzo d'entrata** (es. 4.413,80 → $2.471,73, uscita 24,8 punti sotto) e
  target all'1,9%: mai toccato, le vincenti escono a fine sessione.
- Uscita di fine sessione alle **17:00** NY (template 18-17 giusto); il 19/06 alle 12:59, chiusura
  anticipata per Juneteenth.
- **Commissione impostata a 8.65$** (quella di @EC) invece di 12.5$: non cambia la meccanica, ma
  nello Stage 2 su GC va 12.5$.
