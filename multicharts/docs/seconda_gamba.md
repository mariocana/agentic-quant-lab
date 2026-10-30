# La seconda gamba: cosa deve avere, e dove cercarla

**Decisione del 17/10/2026:** non si parte con una strategia sola. **Almeno due, come test.**
Coerente con Live 004: *"takeaway number one: don't run a single strategy even in the
evaluation phase, that is going to put you at a disadvantage"*.

## Due soglie diverse, e confonderle sarebbe un errore

**Per reggere il conto da sola**, come DriftPullback, servirebbe:

| frequenza | R per micro | avg richiesto | WR | **eccesso sul caso** |
|---|---|---|---|---|
| 1 setup/giorno | $80 o $100 (si semplifica) | $10,12 / $12,65 | 67,5% | **+7,6 pp** |
| 2 setup/giorno | $80 | $5,06 | 63,7% | **+3,8 pp** |
| 3,2 (DriftPullback) | $145 | $5,73 | 63,5% | misurato +2,8 |

Il riferimento: DriftPullback rende **0,1265 R al giorno** per micro. La soglia non dipende da
R, che si semplifica: dipende solo da **quanto spesso opera**.

**Ma una seconda gamba non deve reggere il conto da sola.** Deve **aggiungere**. Live 004 coi
suoi numeri: basket **45,8%** al primo tentativo contro **38%** di una singola, e 84,3% contro
77,2% entro sei. Il guadagno viene dallo **smussamento del percorso**, non dal fatto che ogni
gamba basti.

> **Soglia per la seconda gamba: eccesso positivo e misurato con n sufficiente — almeno 3
> errori standard da zero — piu bassa correlazione con DriftPullback.** Non +7,6.

La controprova e gia agli atti: aggiungere VaultBreak, che sull'OOS aveva edge **zero**,
peggiorava il basket. Serve positivo, non serve enorme.

## Dove cercarla: c'e un'ora completamente libera

Distribuzione oraria degli ingressi di DriftPullback sull'OOS (ora chart, CT):

| ora | trade |
|---|---|
| 09:00 | 415 |
| 10:00 | 546 |
| 11:00 | 248 |
| 12:00 | 131 |
| 13:00 | 77 |
| 14:00 | 22 |

`SessStart` e **09:30**, ma **la sessione RTH apre alle 08:30**.

> **La prima ora, 08:30-09:30 CT, e completamente libera.** Zero trade di DriftPullback.

Una strategia che opera li ha **correlazione quasi nulla per costruzione**, senza doverlo
sperare: non puo essere in posizione nello stesso momento.

## I tre meccanismi mean reverting non ancora provati

Tutti e tre sono **~1 setup al giorno** per costruzione — e il limite che ha ucciso le
candidate IB-C. Ma come *seconda* gamba la soglia e piu bassa, quindi restano in gioco.

| | fonte | dove opera | nota |
|---|---|---|---|
| **Overnight-intraday reversal** | Liu, Liu, Wang, Zhou, Zhu — AsianFA 2025 | **all'apertura** | il meccanismo e la liquidita fornita overnight che viene ripagata intraday. **Cade nell'ora libera** |
| **Gap fade** | Grant-Wolf-Yu 2005; Iwanaga-Sakemoto 2026 | **all'apertura** | cade nell'ora libera, ma le fonti dicono che l'edge si riduce molto coi costi e si indebolisce dopo il 2010 |
| **Morning momentum, afternoon reversal** | Xu, Zhu — SSRN 2022 | pomeriggio | **sovrapposizione piena** con DriftPullback: correlazione alta per costruzione |

**Raccomandazione: overnight-intraday reversal.** Opera nell'ora libera, ha il meccanismo piu
strutturale dei tre (chi fornisce liquidita overnight viene ripagato alla riapertura, come il
VWAP e un benchmark contabile e non una regolarita), ed e la fonte piu recente e cross-asset.
Il gap fade sta nella stessa finestra ma parte con un prior peggiore dichiarato dalle sue
stesse fonti.

## Il metodo resta quello

Prima l'**indicatore di misura**, poi la strategia. E sull'indicatore si controlla che misuri
quello che deve **prima** di leggere il risultato: sul VWAP Fade due bug miei hanno prodotto
prima un −34,66 e poi un −15,47 dove il numero vero era **+0,41**.
