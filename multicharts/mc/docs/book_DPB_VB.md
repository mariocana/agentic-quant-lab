# Book DriftPullback + VaultBreak su LucidFlex 50k (29/10/2026)

**Verdetto: VaultBreak nel book abbassa il pass rate fuori campione.** DPB da sola: 42,2% (iid) e 59,1% (contiguo). Con 1 micro di VB: 40,8% e 53,5%. Con 2 micro: 39,6% e 49,7%.

Script: [`book_sim.py`](book_sim.py). Regole: `prop_firms.ini`, sezione `lucidflex_50k` (MLL $2.000 trailing EOD, DLL $1.200, consistency 40%). Costo: $1 per micro andata e ritorno, misurato sulla dashboard il 27/10.

Report usati:
- **IS:** `DPB_S2_IS_mode0` + `VB_Stage2_IS-intero_costi-onesti`
- **OOS:** `DPB_S5_OOS_2025-2026` + `VB_S5_OOS_2025-2026`

## OOS 2025‑01 → 2026‑10 (456 giorni): il dato che conta

Correlazione del P&L giornaliero DPB/VB: **0,21**.

| book (micro) | net $ | t (giorni) | max DD | giorno peggiore | pass iid | pass contiguo | **edge zero** |
|---|---|---|---|---|---|---|---|
| **DPB 2** (live) | 16.496 | **1,76** | 7.300 | −718 | **42,2%** | **59,1%** | 24,5% |
| VB 2 da sola | −112 | −0,03 | 3.759 | −1.209 | 22,8% | 16,9% | 23,9% |
| DPB 2 + VB 1 | 16.440 | 1,64 | 6.436 | −1.098 | 40,8% | 53,5% | 25,5% |
| DPB 2 + VB 2 | 16.384 | 1,48 | 7.133 | −1.702 | 39,6% | 49,7% | 27,0% |
| DPB 2 + VB 3 | 16.328 | 1,31 | 8.290 | −2.306 | 36,8% | 48,0% | 26,1% |

## IS 2020–2024 (1.275 giorni): solo per confronto

Correlazione: **0,28**.

| book (micro) | net $ | t | max DD | pass iid | pass contiguo | edge zero |
|---|---|---|---|---|---|---|
| DPB 2 | 38.822 | 3,01 | 5.962 | 42,2% | 39,8% | 22,1% |
| DPB 2 + VB 1 | 46.084 | 3,29 | 5.684 | 45,6% | 43,3% | 24,0% |
| DPB 2 + VB 2 | 53.346 | 3,41 | 5.727 | 46,5% | 43,7% | 25,8% |

Sull'IS VaultBreak aiuta (+4 punti), ma è il periodo su cui è stata ottimizzata. Fuori campione l'aiuto sparisce e diventa un costo.

## Cosa dicono i numeri

1. **Il pass rate di VaultBreak da sola (22,8%) coincide con quello a edge zero (23,9%).** Il Monte Carlo la vede come una moneta, coerente con il t −0,03 dello Stage 5.
2. **Una strategia a edge zero non diversifica.** La correlazione è bassa (0,21), ma la diversificazione aiuta solo se ciascuna parte ha un rendimento atteso positivo. Qui VB aggiunge rumore e la giornata peggiore passa da −$718 a −$1.098 / −$1.702.
3. **Il pass rate a edge zero sulle regole Lucid è circa 22–27%, non 40%.** Il conto «target $3.000 contro MLL $2.000 = 40%» vale per un MLL fisso: trailing EOD, consistency e minimo dentro il trade lo abbassano. DPB vale circa **+18 punti** sopra la fortuna.

## Limiti

- **Ordine intraday approssimato:** DPB prima, VB dopo nello stesso giorno. Il drawdown dentro la giornata, con due posizioni aperte insieme, può essere peggiore di quello simulato.
- **VB nella configurazione base** (`MaxTradesPerDay 3`). La variante `MaxTrades1` ha fallito anche lei l'OOS (avg $25 ± 110).
- Il report del corso (Live 4/5) usa 7 micro per strategia su Apex. Qui si confronta alla size che regge l'MLL Lucid.
