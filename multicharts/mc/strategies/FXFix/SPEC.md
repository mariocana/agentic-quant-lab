# FX Fix Reversal (EUR) — Stage 0

**Aperta il 23/10/2026.** Candidata per la seconda gamba, **fuori dagli indici azionari**: gli
effetti intraday sugli indici dipendono dal gamma dei dealer e le 0DTE l'hanno cambiato
(`mc/docs/ricerca_gamma_0dte.md`). Una valuta non e' esposta a quel cambio di regime, ed e'
diversificazione vera rispetto a DriftPullback.

**Fonte:** Krohn, Mueller, Whelan — *Foreign Exchange Fixings and Returns around the Clock*,
*Journal of Finance* 79 (2024), 541-578. Letto il working paper (49 pagine, campione
1999-2018).

## Ipotesi e meccanismo

Molti operatori devono **eseguire al prezzo di fixing** (gestori che ribilanciano, aziende che
regolano, fondi indicizzati). Davanti al fixing c'e' uno **sbilanciamento sistematico di ordini
verso il dollaro**: i dealer lo assorbono, il dollaro **si apprezza prima** del fixing e **si
deprezza dopo**, quando i dealer scaricano l'inventario. Il risultato e' un pattern a W nella
giornata, su tutte e nove le valute del campione.

**Flusso obbligato**: chi deve eseguire al fixing non sceglie l'orario.

## I numeri per l'EUR (Tab. 1, 1999-2018, 5.011 giorni)

Positivo = l'euro si apprezza sul dollaro.

| finestra (ET) | annualizzato | t | per giorno |
|---|---|---|---|
| 17:00 → fixing di Tokyo | −4,93% | −9,19 | |
| Tokyo → 02:00 | +6,14% | 9,27 | |
| **02:00 → fixing BCE 08:15** | **−9,12%** | **−7,13** | **~3,6 punti base** |
| BCE → Londra 11:00 | +1,73% | 1,42 | |
| **Londra 11:00 → 17:00** | **+7,22%** | **6,83** | **~2,9 punti base** |
| giornata intera | +1,04% | 0,47 | |

**Il pattern e' stagionale e non si vede sulla chiusura**: l'euro sulla giornata intera non fa
niente (t 0,47), ma dentro la giornata fa movimenti grandi e opposti.

**Costi, l'esempio del paper**: tradando l'EUR intorno al fixing di Londra, $1 diventa **$15**
dal 1999 al 2018 senza costi, e **piu' che triplica con costi conservativi**, Sharpe netto
**0,65**. Gli autori aggiungono che le oscillazioni *«are not easy to exploit once transaction
costs are accounted for»*.

## Il fixing BCE cambiato nel 2015, e perche' la finestra regge

Nel 2015 la BCE ha spostato la pubblicazione dei suoi tassi di riferimento piu' tardi delle 14:15
CET e li ha resi **solo informativi**. Nel 2016 Reuters ha lanciato il benchmark **WM/Reuters delle
14:00 CET** per le aziende che regolavano sul fixing BCE. **Il flusso obbligato a quell'ora esiste
ancora**, un quarto d'ora prima. Il campione del paper copre il 2015-2018 e il pattern resta.

## Il filtro, compilato

| # | domanda | risposta |
|---|---|---|
| 1 | testato su futures? | **no: su spot** (quotazioni TRTH e transazioni D5). **Deroga motivata**: 6E e EUR/USD spot sono lo stesso sottostante legato dall'arbitraggio; intraday si muovono insieme. Il caso che ha fatto nascere la regola (*Fast Alpha* su SPY che non passava su YM) era un sottostante *diverso*. Il nostro test su 6E e' esattamente la verifica |
| 2 | replicato? | **si'**: nove valute, vent'anni, due fonti dati; e prima Melvin-Prins (2015) ed Evans (2018) sul fixing di Londra |
| 3 | flusso forzato? | **si'**: esecuzione al fixing, rischio d'inventario dei dealer |
| 4 | costi? | **si', in parte**: Sharpe netto 0,65 sull'EUR con costi da interbancario. I nostri sono piu' alti |
| 5 | intraday, flat in sessione? | **si'**: entrambe le finestre stanno dentro la giornata di Lucid (chiusura d'ufficio 16:45 ET) |
| 6 | eta'? | dati fino al **2018**, pubblicato nel 2024: **rischio decadimento** |
| 7 | t ≥ 3? | **si'**: 6,83 e −7,13 |
| 8 | dati oltre il 2021? | **no**. Il nostro IS 2020-2024 e' **interamente fuori dal campione del paper**: e' il test |
| 9 | dati accessibili? | **si'**: solo prezzi |

## Due finestre, pre-registrate entrambe

Sono tutte e due nella tabella del paper e significative: si testano **entrambe**, ciascuna con
la sua soglia, **senza scegliere la migliore dopo**.

| | finestra | posizione | ora CT | ora italiana |
|---|---|---|---|---|
| **A** | dopo Londra | **LONG 6E** | dal fixing di Londra alle **15:40** (5 minuti prima della chiusura d'ufficio Lucid) | pomeriggio-sera |
| **B** | prima della BCE/WMR | **SHORT 6E** | **01:00 → 07:15** (02:00-08:15 ET) | **08:00 → 14:15** |

**B non si sovrappone a DriftPullback ne' come strumento ne' come orario.** A si sovrappone come
orario, non come strumento.

**Ora legale**: il fixing di Londra e' alle 16:00 di Londra, cioe' alle 11:00 ET **tranne** nelle
2-4 settimane all'anno in cui Stati Uniti e Regno Unito cambiano ora in date diverse (marzo e fine
ottobre), quando cade alle 12:00 ET. Il codice deve calcolarlo con le regole reali delle due ore
legali, non con un orario fisso: entrare prima del fixing vorrebbe dire entrare nella fase in cui
il dollaro si apprezza, cioe' contro.

## Il problema strutturale: la dimensione del contratto

Su Lucid **non ci sono micro sulle valute**: 6E e' il contratto intero, **$125.000** di nozionale.
Un punto base vale circa **$13,50**, un tick **$6,25**.

| | finestra A | finestra B |
|---|---|---|
| lordo per giorno, a edge intatto | ~$39 | ~$49 |
| costo round-turn ($2,40/lato Lucid + 1 tick di slippage per lato) | ~$17 | ~$17 |
| **netto a edge intatto** | **~$21** | **~$31** |
| netto a edge dimezzato | ~$2 | ~$7 |

**A edge dimezzato i costi se lo mangiano quasi tutto.** E la variabilita' di un contratto intero
in una finestra di 6 ore e' dell'ordine di **$250-300 al giorno** (stima da una volatilita'
annua dell'EUR del 6-9%): non si puo' scendere sotto un contratto, quindi la combinazione con
DriftPullback va verificata nel simulatore, non assunta.

## Strumento, campione, soglie

| | |
|---|---|
| strumento | **6E**, chart **Globex 24h**, timezone Exchange (CT), 5 min |
| costi | **$2,40/lato** (Lucid) + 1 tick ($6,25) di slippage per lato nel codice |
| IS | **2020-2024** — interamente successivo al campione del paper |
| OOS | **2025-2026, una volta** |
| Gate 2 | **t ≥ 2** per ciascuna finestra |

**Potenza**: il t del paper su 20 anni, riportato a 5, vale **~3,4** (A) e **~3,6** (B) a edge
intatto, **~1,7-1,8** a edge dimezzato. Il Gate 2 passa se e' sopravvissuto almeno il ~55-60%.

## Aspettativa dichiarata

**Una delle due passa, probabilmente la B.** Motivo: il fixing di Londra e' il piu' studiato e
il piu' noto ai market maker — Melvin-Prins e Evans lo documentano gia' nel 2015-2018 — quindi il
piu' esposto all'arbitraggio dopo la pubblicazione. La finestra mattutina e' meno citata.

**E se passano entrambe, il problema diventa la dimensione del contratto**, non l'edge.
