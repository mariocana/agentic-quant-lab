# Cosa uccide le strategie: il pattern di otto morti

Aggiornato al **17/10/2026**. Nove candidate, **una viva**.

## Dove muoiono

| gate | quante | chi |
|---|---|---|
| **Gate 2** — l'edge esiste? | **5** | VWAP Pullback · Gold Asian Range · NQ First5 · BTC First30 · ON Reversal |
| **Gate 5** — regge fuori campione? | **2** | ORB Breakout · VaultBreak |
| **Gate 1** — misura preliminare | 1 | VWAP Fade |
| **viva** | 1 | **DriftPullback** |

**Cinque su otto muoiono alla prima vera domanda.** Non per overfitting, non per regime, non
per costi: l'edge **non c'era mai**.

## Le tre cause, in ordine di frequenza

### 1. Non c'e edge (5 su 8)

L'eccesso sul caso — win rate osservato meno win rate di un random walk con la stessa
geometria — sta intorno a zero:

| | eccesso |
|---|---|
| VWAP Pullback (base) | +0,4 pp |
| VWAP Fade (YM+NQ, 7.516 setup) | **−0,62 pp** |
| ON Reversal (1.175 risolti) | +0,68 pp |

E il metro giusto, perche' **non dipende dalla geometria**: cambiare il rapporto
target/stop rietichetta l'edge, non lo crea. La letteratura documenta +1,5…+5 pp; il nostro
massimo e' **+5,3** (VaultBreak) e il sopravvissuto sta a **+2,8** (DriftPullback).

### 2. L'edge c'e ma svanisce fuori campione (2 su 8)

| | IS | OOS |
|---|---|---|
| VaultBreak base | t 2,40 | **−0,03** |
| VaultBreak MaxTrades1 | t 2,88 | **0,23** |
| ORB cutoff11 | t 2,80 | **0,63** |

Su ORB era **scritto prima**: nello split-sample il filtro guadagnava +21% nella prima meta'
dell'IS e **+2,5% nella seconda**. Era un adattamento al 2020-2022, e il 2025-2026 lo ha
mostrato.

### 3. L'edge c'e, regge, e non basta per il conto (0 su 8 finora)

DriftPullback e' arrivata qui e **ha passato** lo Stage 7 (42% per tentativo). Nessuna e'
ancora morta per questa ragione — ma ORB ci sarebbe arrivata: **$878/anno per micro** contro
$3.000 di target sono 3,4 anni.

## Il discriminante vero: frequenza x edge, non edge

| | eccesso | trade/giorno | **$/giorno per micro** | esito |
|---|---|---|---|---|
| **DriftPullback** | +2,8 pp | **3,2** | **$18,34** | **viva** |
| VaultBreak | **+5,3 pp** | ~0,6 | — | morta OOS |
| ON Reversal | +0,68 | 0,83 | negativo | morta |

**VaultBreak aveva quasi il doppio dell'eccesso di DriftPullback ed e' morta.** Quello che
distingue la sopravvissuta non e' la qualita' del singolo trade: e' **quante volte opera**.

La soglia derivata: **sotto $10 al giorno per micro non si parte**, e a 1 setto al giorno
servirebbe un eccesso di **+7,6 pp** che non abbiamo mai visto nemmeno una volta.

## Dove ho sbagliato io, che e' meta' della lezione

| | errore | come si e' visto |
|---|---|---|
| **3 volte** | bug nell'indicatore di misura | confrontando misura e backtest |
| 2 volte | previsione sullo strumento | RTY batteva YM (no), MCL ~$200 di range (era $170) |
| 1 volta | etichetta di famiglia | VWAP Pullback era momentum, non mean reverting |

I tre bug: **riarmo mancante** (15,65 setup/giorno invece di 3,3), **caso calcolato sulla
geometria di progetto** invece che su quella realizzata (−15,47 dove c'era +0,41), e
**tie-break verso il target** nella stessa barra piu' **non risolti esclusi** (+4,40 promesso,
−$40.784 reale).

I primi due li ho presi **perche' avevo messo una diagnostica**. Il terzo no, perche' la
diagnostica che serviva non l'avevo pensata.

> **Un indicatore di misura non autorizza una strategia. Al massimo la propone.**

## Le tre cose che hanno funzionato davvero

1. **Scrivere soglia, attesa e kill PRIMA del run.** Su ORB la riserva scritta il 29/09 si e'
   avverata il 17/10. Senza, il numero lo si sarebbe spiegato.
2. **I controlli preliminari automatici.** Hanno intercettato tre run invalidi di VaultBreak
   (range corto, compressione sbagliata) che altrimenti avremmo letto come verdetti.
3. **L'eccesso sul caso come metro.** E' l'unica misura che non si lascia ingannare dal
   rapporto target/stop, ed e' quella che ha smascherato il PF come criterio da conto reale.
