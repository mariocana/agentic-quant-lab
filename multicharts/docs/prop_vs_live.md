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
| **ORB (cutoff11)** | 550 | 58,9% | 0,93 | $189 | **2,95** | Gate 3: DD 95° ÷10 $3.121 vs $2.000 | **mai giudicata** |
| **DriftPullback** | 3499 | 63,5% | 0,64 | $55 | **3,01** | Gate 2: WR 63,5% vs soglia nostra 70% (RATIO) | **mai giudicata** |

Tre erano morte davvero: nessun edge, t sotto 1. Una e morta come si deve: OOS.
**Due sono state uccise da criteri che il corso assegna ai soldi propri.**

DriftPullback ha WR 63,5% — **dentro la banda 54-72% del corso** e praticamente uguale al
~65% dell'esempio che deploya — avg netto $55 contro $77, e il t piu alto che abbiamo mai
misurato su 3.499 trade e cinque anni.

**Precisazione sulla sua causa di morte, perche cambia il senso.** Non l'ha uccisa il PF
1,12: l'ha uccisa una soglia **WR >= 70%** che avevamo pre-registrato noi, derivata dalla
nostra formula di fattibilita `RATIO = E x DDcap / (DD_R x (soglia + costo))`. Due problemi:

1. Il termine `soglia` in quel denominatore **e** il criterio live dei $7/micro. La formula
   si portava dentro il criterio che stiamo togliendo.
2. Piu grave: la formula chiede che la strategia **sopravviva al drawdown storico di cinque
   anni** con il rischio compresso dentro l'MLL. Ma una eval non e quello. E un **primo
   passaggio su una finestra corta, ripetibile su piu tentativi**: probabilita di toccare
   +$3.000 prima di -$2.000. Non serve sopravvivere a cinque anni, serve non incrociare la
   soglia durante il tentativo — e se lo incroci, ne compri un altro a $100.

Il RATIO rispondeva con una formula alla domanda che il corso affida al **simulatore**
(Stage 7), e la rispondeva nella versione piu severa possibile. Per questo lo Stage 7 lo
sostituisce. **Nota onesta:** l'obiezione economica del RATIO non e nulla — con DD_R 25,5 e
R <= $78/micro l'edge netto vale ~$2,24/trade, cioe ~$1.568/anno per micro contro $3.000 di
target, e il rapporto non migliora aumentando i micro perche scalano entrambi. Ma quella e
una stima su percorso medio e singolo tentativo. **La risposta vera la da la simulazione
sull'OOS, ed e il motivo per cui DriftPullback va in OOS invece di restare archiviata.**

Costi gia dentro: commissione $7,50/contratto/lato + 2 tick di slippage sullo stop.

## Conseguenza operativa

Nessun criterio nuovo. Si **togliono** da Gate 2 i tre criteri live e si rimettono dove
servono, in un documento in stand-by da riesumare quando i payout iniziano e il conto si
forma. E la prossima strategia non va cercata: e **DriftPullback**, che ha un edge misurato
e non ha mai visto un out-of-sample.

## Perche le altre quattro restano morte — t su *tutte* le varianti girate

Non su una configurazione scelta: su ogni report in archivio.

| strategia | varianti | miglior t su IS 5 anni | WR della variante migliore | verdetto |
|---|---|---|---|---|
| **VWAP Pullback** | 9 | **0,87** (meta2 base, n=391) | 58,1% | **morta senza ambiguita.** Lo Stage 1 era *negativo*: t −1,54. Nessuna variante si avvicina |
| **Gold Asian Range** | 7 | **1,89** (A tp0, n=1280) | **42,6%** | **morta di forma, non di t.** L'unica variante con t quasi significativo ha WR 42,6%, **fuori dalla banda 54-72%** e R:R > 1 → serie perdenti lunghe, cioe esattamente il nemico dichiarato. La variante con WR giusto (B, 52,7%) ha t 0,92. Mai entrambe |
| **NQ First5** | 14 | **1,63** (filtrata, n=294) | 53,1% | **debole e fuori banda.** IS intero t 1,00 con WR 51,4%; meta1/meta2 1,15 e 1,19. Sotto la banda su tutte le varianti |
| **VaultBreak** | 13 | 2,63 base / **2,97** MaxTrades1 | 63,1% / 65,4% | **l'unica falsificata come vuole il corso** — ma vedi sotto |

Reggono anche con la soglia piu permissiva del corso (t ≥ 1,28, il livello «≤10% simulazioni
negative»): VWAP 0,87, Gold-B 0,92, First5 1,00 restano sotto comunque.

### Una cosa su VaultBreak, da verificare

L'OOS girato (`VB_S5_OOS_2025-2026`) ha **n = 295 su due anni ≈ 145 trade/anno**, che
corrisponde alla configurazione **base** (723 trade / 5 anni = 145/anno), **non** a
`MaxTrades1` (384 / 5 anni = 77/anno), che ha t **2,97**, WR 65,4%, PF 1,40, avg $167.

Quindi l'OOS ha falsificato la config base. **`MaxTrades1` non ha mai visto un OOS.** Da
tenere presente: non e una resurrezione automatica — i suoi trade sono un sottoinsieme
selezionato *in sample* di quelli della base, e la base OOS ha edge zero. Ma e un run da
dieci minuti, e va fatto **dopo** DriftPullback, una alla volta.
