# Prop e Live sono due metodologie diverse

**Data:** 15/10/2026 · **Fonte:** `education/protocollo/transcripts/*PROPFIRMS_AS_A_BUSINESS_Live_00[1-5]*`

## Il corso le separa esplicitamente

> *"This is extremely important when you're trading with **your own capital** rather than
> when you're trading with prop firms. Because with prop firms it's just a game. Like you
> shouldn't trade with prop firms to get rich, but you should trade to have access to
> virtual capital."* — Live 001, 823-828

Il contesto di quella frase e la robustezza al cambio di regime: serve **per i soldi
propri**, non per superare una eval.

> *"Your biggest enemy is the trailing drawdown and **not the profit factor**, the profit
> target."* — Live 002, 273

## Cosa controlla davvero il corso prima di decidere (Live 003, 23-50)

Quattro numeri, e poi la simulazione:

1. time range
2. numero di trade
3. **win rate**
4. **average trade**

Poi: *"it's the first analysis on the **out of sample** data"* → simulazione di
first-passage sull'OOS → output = **pass rate** e **numero ottimo di contratti**.

Non c'e profit factor. Non c'e un tetto al drawdown di nostra invenzione. Non c'e
concentrazione annuale. Il drawdown entra **solo** come MLL dentro la simulazione.

### Il livello che il corso considera lavorabile

| Live | pass rate / tentativo | cumulato |
|---|---|---|
| 003, 107 | **39%** | — |
| 004, 237-238 | **47,9%** | **92,6% entro 4 tentativi** |
| 004, 52 | — | 75% entro 2 tentativi |

Il 39% per tentativo e considerato accettabile perche si compone sui tentativi. Il nostro
Gate 2 pretendeva una strategia molto piu forte di quella che il corso deploya.

### Il profilo, misurato dal corso stesso (Live 002, 244-252)

> *"we have an average trade net of **77**. It's not huge, but the edge here is not in a
> single trade, is in consistency and repetition"* · *"a very high win rate ... around **65%**"*

E Live 005, 1585: *"win rate between **54 and 72** percent"*.

## Lo split

| criterio | dove appartiene | perche |
|---|---|---|
| WR alto (54-72%) | **PROP** | profilo dichiarato, Live 005 |
| R:R basso (0,5-1) | **PROP** | corollario del WR alto |
| t sull'OOS | **PROP** | Live 002 cita t = 2,229 OOS |
| n, time range | **PROP** | Live 003, 23 |
| pass rate (+ cumulato sui tentativi) | **PROP** | e *il* criterio di decisione |
| trailing drawdown / MLL | **PROP** | vincolo dentro la simulazione, non gate |
| contratti e rischio = output | **PROP** | Live 001, 359 |
| piu strategie poco correlate | **PROP** | Live 001, 421: trend following + mean reverting |
| **PF >= 1,2** | **LIVE** | Live 002, 273 dice il contrario per la prop |
| **avg trade >= $70** | **LIVE** | numero da *guardare*, non soglia (Live 002, 245) |
| **nessun anno > 50%** | **LIVE** | consistenza di lungo periodo |
| robustezza al cambio di regime | **LIVE** | Live 001, 823 |
| ragione strutturale dell'edge | **LIVE** | idem |
| drawdown a 5 anni | **LIVE** | idem |

## Il conto di quello che ci e costato

Sei strategie, sei morti. Rigiudicate col solo metro prop:

| strategia | n | WR | R:R | avg netto | t (IS) | causa morte | verdetto metro prop |
|---|---|---|---|---|---|---|---|
| VWAP Pullback | 764 | — | — | — | **0,23** | Gate 2 | **morta** — nessun edge |
| Gold Asian Range | 1280 | — | — | $21 | **0,92** | Gate 2 | **morta** — nessun edge |
| NQ First5 | 1291 | — | — | $87 | **1,00** | Gate 2 | **morta** — nessun edge |
| VaultBreak | 723 | — | — | — | 2,63 IS → **-0,03 OOS** | OOS | **morta** — l'unica falsificata come vuole il corso |
| **ORB (cutoff11)** | 550 | 58,9% | 0,93 | $189 | **2,95** | Gate 3 (nostro) | **mai giudicata** |
| **DriftPullback** | 3499 | 63,5% | 0,64 | $55 | **3,01** | Gate 2: PF 1,12 e avg $55 | **mai giudicata** |

Tre erano morte davvero: nessun edge, t sotto 1. Una e morta come si deve: OOS.
**Due sono state uccise da criteri che il corso assegna ai soldi propri.**

DriftPullback ha WR 63,5% contro il ~65% dell'esempio che il corso deploya, avg netto $55
contro $77, e il t piu alto che abbiamo mai misurato su 3.499 trade e cinque anni. L'abbiamo
fermata per PF 1,12 — cioe per il numero che Live 002 chiama esplicitamente *non* il nemico.

Costi gia dentro: commissione $7,50/contratto/lato + 2 tick di slippage sullo stop.

## Conseguenza operativa

Nessun criterio nuovo. Si **togliono** da Gate 2 i tre criteri live e si rimettono dove
servono, in un documento in stand-by da riesumare quando i payout iniziano e il conto si
forma. E la prossima strategia non va cercata: e **DriftPullback**, che ha un edge misurato
e non ha mai visto un out-of-sample.
