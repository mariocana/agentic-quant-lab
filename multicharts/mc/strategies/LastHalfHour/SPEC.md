# Last Half-Hour Momentum — Stage 0

**Aperta il 18/10/2026.** Candidata per la seconda gamba, scelta col filtro di
`mc/docs/come_scegliere_un_paper.md`.

**Fonte:** Baltussen, Da, Lammers, Martens — *Hedging demand and market intraday momentum*,
*Journal of Financial Economics* 142 (2021), 377-403. Letto per intero (27 pagine).

## Ipotesi e meccanismo

Chi e' **corto gamma** — i market maker delle opzioni sull'indice, i fornitori di ETF a leva —
per coprirsi deve **comprare quando il mercato sale e vendere quando scende**, e concentra la
copertura **a fine giornata**. Il risultato: il rendimento della **mezz'ora finale** ha lo
stesso segno di quello del resto della giornata.

**E' un flusso obbligato**, non un pattern: il market maker non sceglie se coprirsi. Il paper
lo verifica direttamente: l'effetto e' **piu' forte quando l'esposizione gamma netta e' piu'
negativa** (proxy costruito sulle opzioni S&P 500).

## Il filtro, compilato

| # | domanda | risposta | fonte nel paper |
|---|---|---|---|
| 1 | testato su futures? | **si'**: ES, NQ, YM, RTY singolarmente, piu' 60 altri | Tab. B1 |
| 2 | replicato? | **si'**: estende Gao-Han-Li-Zhou (JFE 2018); 60+ mercati; risultati **simili** nei sottoperiodi 1974-1999 e 2000-2020 | §3.4, Tab. 5 |
| 3 | meccanismo di flusso forzato? | **si'**: gamma hedging, verificato condizionando sull'esposizione netta | §4 |
| 4 | costi? | **no**: *«we do not consider transaction costs»*. Unica frase: su ES il Sharpe netto resta **positivo** con un costo di **un tick** | p. 386 |
| 5 | intraday, flat in sessione? | **si'**: si entra 30 minuti prima della chiusura e si esce in chiusura. **1 segnale al giorno, tutti i giorni** | eq. 12 |
| 6 | eta'? | dati fino a **maggio 2020**, pubblicato nel **2021**: siamo oltre il picco di decadimento | — |
| 7 | t ≥ 3? | **si' su tutti e quattro** (vedi sotto) | Tab. B1 |

**Passa i tre eliminatori.** Il punto debole e' il 4.

## I numeri, per mercato

Regressione individuale, predittore `r_ROD`, rendimento predetto quello della mezz'ora finale:

| | t | R² | R² fuori campione | campione |
|---|---|---|---|---|
| **NQ** | **7,97** | 4,10% | 3,76% | 1996-2020 |
| RTY | 5,86 | 3,35% | 3,15% | 1993-2020 |
| ES | 4,97 | 3,41% | 2,29% | 1982-2020 |
| YM | 4,12 | 2,20% | 2,18% | 1997-2020 |

**NQ e' il piu' forte dei quattro**, coerente col fatto che anche DriftPullback funzioni li' e
non su YM.

Strategia del paper, portafoglio equipesato dei futures azionari, **senza costi**: rendimento
annuo **6,86%**, Sharpe **1,73**, **successo 55%** dei giorni. Con il filtro «entrambi i
segnali concordi»: successo **61%**, Sharpe 1,60.

## Perche' NQ, e perche' e' deciso prima di guardare

**Il nostro IS e' di cinque anni; il paper ne usa da 23 a 38.** Il t scala con la radice del
numero di osservazioni, e con 1.258 sessioni nel 2020-2024:

| | t atteso, edge intatto | t atteso, edge dimezzato |
|---|---|---|
| **NQ** | **3,64** | **1,82** |
| RTY | 2,53 | 1,27 |
| ES | 1,81 | 0,90 |
| YM | 1,95 | 0,97 |

> **Su cinque anni, solo NQ puo' superare il Gate 2 (t ≥ 2) anche se l'effetto e' ancora
> tutto li'.** ES e YM non ce la farebbero nemmeno a edge intatto: un loro fallimento non
> direbbe niente.

Quindi **NQ, scelto a priori**. Non si girano i quattro per poi tenere il migliore: sarebbe
selezione sugli stessi dati.

**E c'e' un vantaggio che il paper ci regala:** il suo campione finisce a **maggio 2020**. Il
nostro IS 2020-2024 e' quasi interamente **successivo alla pubblicazione dei dati**. Non stiamo
ottimizzando niente — la strategia non ha parametri — e stiamo misurando esattamente il
decadimento post-pubblicazione di McLean-Pontiff.

## Regole, pre-registrate

```
segnale  r_ROD = Close alle 14:30 CT  /  chiusura RTH di ieri (15:00 CT)  - 1
         (overnight compreso: e' la definizione del paper)
ingresso alle 14:30 CT, a mercato:   LONG se r_ROD > 0,   SHORT altrimenti
uscita   alle 15:00 CT, a mercato    (la chiusura della sessione cash)
```

- **Nessuno stop nel test.** La strategia del paper non ne ha, e aggiungerne uno cambierebbe
  la cosa che stiamo verificando. **Il rischio lo misura lo Stage 7**, che usa l'escursione
  dentro il trade (`Drawdown ($)`) contro l'MLL.
- **Nessun parametro.** Non c'e' niente da ottimizzare, quindi niente da fissare sull'IS.
- **Giorni a chiusura anticipata** (vigilie di festa, chiusura alle 12:15 CT): **nessun
  trade**. Se non esiste la barra delle 14:30, non si entra.
- **Il filtro «entrambi i segnali concordi» NON si testa.** E' nel paper, ma provarlo sugli
  stessi dati dopo la versione base sarebbe scegliere il migliore fra due.

| | |
|---|---|
| strumento | **@NQ, 5 min**, Globex 24h, timezone Exchange (CT), Bar Magnifier 1 min |
| costi | **$7,50/lato** (convenzione NQ: $1,75 Lucid + slippage) |
| IS | **2020-2024** |
| OOS | **2025-2026, una volta** |

## Soglie e kill

| | soglia | t atteso, edge intatto / dimezzato |
|---|---|---|
| **Gate 2** (IS) | **t ≥ 2** | 3,64 / 1,82 |
| **Gate 5** (OOS, ~450 sessioni) | **t ≥ 1,3** | 2,18 / 1,09 |

**Lettura pre-registrata:** il Gate 2 passa se dell'edge e' sopravvissuto **almeno il ~55%**.
Sotto, l'effetto e' decaduto oltre quanto la letteratura fa aspettare, e si chiude.

**Il WR/R:R del profilo prop non si applica come kill**: la strategia esce a tempo, non con un
bracket. Si guarda il **segno** (successo contro 50%) **e la mossa media nei due casi** — la
lezione dell'oro: un segno significativo con ampiezze asimmetriche puo' avere expectancy zero.

## Aspettativa dichiarata

**Effetto dimezzato**, cioe' **t intorno a 1,8 sull'IS: sotto la soglia.** E' quello che
McLean-Pontiff fanno aspettare dopo la pubblicazione, e i dati dal 2020 vengono dopo
un'esplosione di opzioni 0DTE che ha cambiato il posizionamento gamma dei dealer — in una
direzione che non so prevedere.

**Il dubbio da tenere aperto**: 0DTE potrebbe aver **rafforzato** l'effetto (piu' copertura
intraday) o **spostato** la copertura prima della mezz'ora finale. Il test lo dira'.

## Correlazione con DriftPullback

Stesso strumento, famiglia simile (momentum), **finestra diversa**: DriftPullback ha
**22 ingressi su 1.439** nell'ora delle 14:00 nell'OOS, e chiude alle 14:55. **Si misura dopo
il Gate 2**, non si assume.
