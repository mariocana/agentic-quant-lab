# CHECKLIST Stage 1 — MondayLong

Codice: `MondayLong.txt`, in MultiCharts **`Mario_MondayLong`** (Signal). SPEC:
`SPEC.md` (pre-registrata, commit 3bb4733). Lo Stage 1 controlla solo la meccanica: il
risultato in dollari non conta.

## Chart

| | |
|---|---|
| Simbolo | **@ES** continuo |
| Timeframe | **5 minuti** |
| Sessione | **CME Globex 17:00-16:00 CT senza pause** (non RTH, non un template con la pausa 15:15-15:30) |
| Timezone | **Exchange (CT)** |
| Barre | timbrate alla chiusura |
| Bar Magnifier | **attivo, 1 minuto** |
| IOG | off |
| Commissione | **$15 per contratto per lato** (slippage incluso) |
| Slippage | **0** |
| Point value | $50 (verificalo nel foglio Settings del report) |
| Periodo del chart | **dal 02/01/2020 al 29/05/2020**: il chart parte un mese prima, così il primo ingresso (domenica 02/02) non cade nelle barre del Max bars back |
| Finestra valutata | `TradeStartEL 1200201` · `TradeEndEL 1200529`, cioè **01/02/2020 → 29/05/2020** (date della sessione, il lunedì) |

Input ai default della SPEC: `EntryTime 1900`, `ExitTime 1555`, `SessionWeekday 1`,
`StopPts 90`, `TargetPts 100`. Si cambiano solo `NumContracts` e `ShowLog`.

## Run

| run | `NumContracts` | `ShowLog` | file da esportare in `reports/` |
|---|---|---|---|
| A | 1 | **1** | `ML_S1_x1.xlsx` + log dell'Output di PowerLanguage salvato come `ML_S1_log.txt` |
| B | 10 | 0 | `ML_S1_x10.xlsx` |

Il report va esportato **dopo** il commit della SPEC (`lab.py` controlla l'Export Time).

## Cosa deve uscire

**15 trade**, uno per ogni lunedì non festivo. Nella List of Trades l'ingresso porta la data e
l'ora della **domenica alle 19:00**:

| domenica d'ingresso | lunedì della sessione | nota |
|---|---|---|
| 02/02, 09/02, 23/02 | 03/02, 10/02, 24/02 | |
| 01/03 | 02/03 | |
| **08/03** | 09/03 | **cambio dell'ora legale**: l'ingresso deve restare alle 19:00 CT |
| 15/03, 22/03, 29/03 | 16/03, 23/03, 30/03 | il 15/03 ES era limit down in Globex: vedi sotto |
| 05/04, 12/04, 19/04, 26/04 | 06/04, 13/04, 20/04, 27/04 | |
| 03/05, 10/05, 17/05 | 04/05, 11/05, 18/05 | |

**Nessun ingresso** domenica 16/02 (lunedì 17/02, Presidents' Day) e domenica 24/05 (lunedì
25/05, Memorial Day): nel log del run A ci devono essere due righe `ML SKIP` con quelle date.

Se manca un trade, guarda sul chart se la barra delle 19:00 di quella domenica esiste: una barra
mancante nei dati non è un bug del codice, ma va scritta qui.

## Controlli (il judge li fa con `lab.py giudica ... s1`)

Valori per i controlli automatici:

| controllo | valore |
|---|---|
| finestra degli orari d'ingresso, come li scrive MC (chiusura della barra del fill) | **`--entrata 1900-1900`** |
| trade massimi al giorno (per data d'ingresso) | **`--max-giorno 1`** |
| flat la sera | **no: non passare `--flat`**. Il trade entra la domenica ed esce il lunedì, è a cavallo di due date per costruzione. Il flat che conta è il punto 4 sotto |
| stop in punti | **−90,00** (`Stop Loss`) |
| target in punti | **+100,00** (`Profit Target`) |

```bash
python3 docs/lab.py giudica strategies/MondayLong/SPEC.md s1 strategies/MondayLong/reports/ML_S1_x1.xlsx \
    --x10 strategies/MondayLong/reports/ML_S1_x10.xlsx --entrata 1900-1900 --max-giorno 1
```

| # | controllo (SPEC) | come si verifica |
|---|---|---|
| 1 | ingressi solo la domenica alle 19:00 CT, 15 trade, date della tabella sopra | List of Trades + righe `ML ENT` del log |
| 2 | festivi esclusi | due righe `ML SKIP` (16/02 e 24/05), nessun trade in quelle sessioni. Le righe `ML CAL` del log elencano il calendario 2020-2021: 17/02/2020 e 25/05/2020 devono esserci |
| 3 | uscite solo di tre tipi: `Stop Loss` a −90,00 punti, `Profit Target` a +100,00, `ML-Time` alla barra delle **15:55** del lunedì | riepilogo delle uscite di `lab.py` + righe `ML EXIT`. `ML-Safety` deve comparire **zero** volte |
| 4 | **nessuna posizione dopo le 16:00 CT del lunedì** | ogni uscita ha data = lunedì della sessione e ora ≤ 16:00; le uscite a tempo sono tutte alle 15:55 (16:00 solo se la barra delle 15:55 manca, da annotare). Nessuna uscita il martedì, nessun `ML-Safety` |
| 5 | stop e target calcolati dal prezzo d'ingresso | su 3 trade a mano: `SL` e `TP` della riga `ML ENT` = close della barra delle 19:00 − 90 e + 100; in P&L a 1 contratto lo stop vale **−$4.530** (90 × $50 + $30) e il target **+$4.970** |
| 6 | stop attivo dalla barra dopo l'ingresso, non prima | nessuna uscita timbrata alle 19:00 della domenica |
| 7 | scaling ×10 | run B: stessi 15 trade, stessi ingressi e uscite, P&L esattamente ×10 su ogni trade, commissioni ×10 ($450 → $4.500). `SetStopContract` rende stop e target per contratto: se B non scala, è un bug |

**Stop oltre i 90 punti.** Con Bar Magnifier lo stop si riempie al suo prezzo, salvo che la barra
a 1 minuto apra già oltre: allora il fill è all'apertura e i punti sono peggiori di −90. In
questo periodo può succedere il 15-16/03/2020 (limit down in Globex, riapertura con gap). Non è
un bug: si annota data e punti. È esattamente il caso che in fase 2 fa scattare il kill del
trade peggiore > $500 per micro, se si ripete nell'IS.

## Cosa guardare sul grafico

- Domenica **08/03/2020**: la freccia d'ingresso sulla barra delle 19:00 CT, non sulle 18:00 o
  sulle 20:00 (cambio dell'ora legale quella notte).
- Domenica **15/03/2020**: se c'è la barra delle 19:00 e a che prezzo entra; dove e quando esce.
- Un'uscita `ML-Time`: sulla barra delle 15:55 del lunedì, e dopo nessuna posizione aperta fino
  alla domenica successiva.
- Un `Stop Loss` e, se c'è, un `Profit Target`: livello = ingresso − 90 / + 100.
- Domenica 16/02 e 24/05: nessuna freccia.

## Dopo lo Stage 1

IS: stesso chart dal **01/12/2019 al 31/12/2024**, `TradeStartEL 1200101`, `TradeEndEL
1241231`, 1 contratto, `ShowLog 0`, file `reports/ML_IS_2020-2024.xlsx`. Attesi 232 trade.
Solo dopo il verdetto Stage 1 `passa`.
