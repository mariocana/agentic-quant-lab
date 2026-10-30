# Direzione di ricerca: gli effetti intraday condizionati al gamma dei dealer

**23/10/2026.** E' il primo filone che **spiega** i nostri risultati invece di contraddirli.

## Cosa dice la letteratura recente (dati dal 2022, era 0DTE)

- **Dim, Eraker, Vilkov** — *0DTEs: Trading, Gamma Risk and Volatility Propagation* (SSRN
  4692190): il gamma netto dei market maker e' **in media positivo**, e il gamma positivo
  **rafforza la reversione intraday**.
- **Adams, Fontaine, Ornthanalai** — *Do S&P 500 Options Increase Market Volatility? Evidence
  from 0DTEs*: piu' gamma netto dei dealer → reversione piu' forte nel flusso d'ordini sull'E-mini
  e **momentum negativo** sui rendimenti ad alta frequenza.
- **Baltussen et al.** (JFE 2021, dati fino al 2020): l'effetto di momentum in chiusura e' **piu'
  forte quando il gamma netto e' negativo**.

## Perche' spiega i nostri dati

| | gamma dei dealer | cosa prevede la teoria | cosa abbiamo misurato |
|---|---|---|---|
| fino al 2020 | spesso corto | momentum | LastHalfHour: t 1,49 dentro il campione del paper |
| 2022 | corto (mercato ribassista) | momentum | LastHalfHour 2022: **+$109, t 1,57** |
| 2023-2024 | lungo (era 0DTE) | **reversione** | LastHalfHour 2023-24: **−$36 e −$89**, t −0,81 e −1,37 |

**E spiega anche perche' le nostre mean reversion autonome sono morte** (VWAP fade −0,62 pp,
gap fade +0,68): non condizionate al regime, mescolano giorni di reversione e giorni di momentum,
e la media fa zero.

## I dati ci sono

**SqueezeMetrics** pubblica il GEX giornaliero dell'S&P 500 in un CSV pubblico
(`squeezemetrics.com/monitor/static/DIX.csv`): colonne `date, price, dix, gex`, dal
**2011-05-02** al **2026-10-22**, 3.893 giorni, 223 KB, aggiornato ogni sera.

**Due avvertenze sul dato:**
1. **E' una stima, non il dato dei paper.** Gli autori usano l'open interest per tipo di
   operatore; SqueezeMetrics ricostruisce il gamma con ipotesi proprie (documentate nel loro
   *white paper*). E' un proxy.
2. **E' giornaliero.** Nella strategia si usa il GEX **di ieri sera**, noto prima dell'apertura:
   niente look-ahead.

## L'ipotesi da pre-registrare, se si procede

> Con **GEX di ieri < 0** (dealer corti gamma): momentum intraday.
> Con **GEX di ieri > 0** (dealer lunghi gamma): reversione intraday.

Il test piu' semplice e' su LastHalfHour stesso: **entrare nella direzione del rendimento del
giorno se GEX < 0, contro se GEX > 0.**

**Il problema di contaminazione, da dichiarare:** l'IS 2020-2024 di LastHalfHour l'abbiamo gia'
visto, anno per anno. Lo split per segno del GEX invece **no** — il GEX cambia segno dentro lo
stesso anno — ma sapere che il 2022 era positivo inquina. **Il test che conta e' l'OOS
2025-2026, intatto**, una volta sola.

## Prossimo passo

1. Leggere Dim-Eraker-Vilkov e Adams-Fontaine-Ornthanalai per intero, per fissare orizzonte e
   soglie dai paper e non dai nostri dati.
2. Scaricare il CSV (serve il tuo ok) e misurare **quanti giorni** cadono in ciascun regime dal
   2020: se il GEX e' quasi sempre positivo, il ramo «momentum» ha troppo pochi giorni per essere
   testato.
3. Solo dopo, lo Stage 0.

---

## Controllo dei regimi (23/10/2026): **il ramo «momentum» non si puo' testare**

`DIX.csv` scaricato in `mc/data/squeezemetrics/` (223.372 byte, **fuori da git** — sono dati con
termini d'uso di SqueezeMetrics). Regime di oggi = GEX di **ieri sera**. Contati solo i giorni:
**non incrociati coi trade di LastHalfHour**, per non guardare il risultato condizionato prima
di pre-registrarlo.

| anno | GEX < 0 | GEX > 0 | % negativi |
|---|---|---|---|
| 2016 | 22 | 230 | 8,7% |
| 2017 | 2 | 249 | 0,8% |
| 2018 | 38 | 213 | 15,1% |
| 2019 | 19 | 233 | 7,5% |
| 2020 | 31 | 222 | 12,3% |
| 2021 | 16 | 236 | 6,3% |
| **2022** | **104** | 147 | **41,4%** |
| 2023 | 23 | 227 | 9,2% |
| **2024** | **1** | 251 | **0,4%** |
| 2025 | 9 | 241 | 3,6% |
| 2026 | 9 | 194 | 4,4% |

| blocco | GEX < 0 | GEX > 0 |
|---|---|---|
| **IS 2020-2024** | **175** (104 nel solo 2022) | 1.083 |
| **OOS 2025-2026** | **18** | 435 |

Livello dal 2020, in miliardi: p5 **−1,13**, p25 1,77, **mediana 4,31**, p75 6,38, p95 9,97.

### Potenza

Con la deviazione per trade di LastHalfHour (**$990**), il t raggiungibile:

| ramo | n | avg $50 | avg $100 | avg $150 |
|---|---|---|---|---|
| GEX < 0, IS | 175 | 0,67 | 1,34 | 2,00 |
| **GEX < 0, OOS** | **18** | 0,21 | **0,43** | 0,64 |
| GEX > 0, IS | 1.083 | 1,66 | 3,32 | 4,99 |
| GEX > 0, OOS | 435 | 1,05 | 2,11 | 3,16 |

### Tre conseguenze

**1. Il ramo «momentum quando il gamma e' negativo» e' morto come test.** Nell'OOS ci sono **18
giorni**: anche con un edge da $100 a trade si arriva a **t 0,43**. E nell'IS quel ramo e', per
il 60%, **il 2022 — che abbiamo gia' visto** (+$109).

**2. Il segno del GEX, oggi, non filtra quasi niente.** Dal 2023 e' positivo il **96%** dei
giorni. «Reversione quando il gamma e' positivo» equivale in pratica a **«reversione sempre»**.

**3. L'unico condizionamento che ha senso e' sul LIVELLO, non sul segno.** I paper dicono che
**piu' gamma = piu' reversione**: una relazione dose-risposta. Dividere i giorni per terzili di
GEX (con la mediana a 4,3 miliardi c'e' parecchia dispersione) e verificare che la reversione
**cresca col livello** e' un test del **meccanismo**, molto piu' forte di un test sul segno.

### L'avvertenza che pesa di piu'

**Nel 2020-2024 l'86% dei giorni aveva gamma positivo, e le nostre mean reversion — VWAP fade e
gap fade — hanno dato zero.** E' un indizio **contro** una reversione sfruttabile alle nostre
frequenze. Se il fenomeno dei paper esiste, sta su un **orizzonte** o su un **livello di GEX**
che i nostri test non hanno colto — oppure e' cosi' piccolo che i costi lo mangiano, come dice
*Fast Alpha* per la reversione a breve.

**Prima di scrivere qualunque Stage 0, va letto l'orizzonte nei paper**: se la reversione che
documentano e' a 10 minuti e in punti base, per noi non esiste.

---

## Incrocio VWAP fade × GEX (23/10/2026) — indizio, non misura

Log giornalieri del VWAP fade 2020-2024 (versione col riarmo corretto) incrociati col GEX della
sera prima, per terzili calcolati sull'IS. **Avvertenza registrata prima di guardare**: il
misuratore aveva due distorsioni legate alla volatilita' (sforamento d'ingresso che abbassa il
caso, tie-break che gonfia le vincite), di segno opposto, e il GEX basso coincide coi giorni
volatili. Si legge solo la differenza fra terzili, e con cautela.

| GEX di ieri | YM: WR risolti | NQ: WR risolti |
|---|---|---|
| basso (< 2,08 mld) | 42,91% | **40,38%** |
| medio | **47,37%** | 42,96% |
| alto (≥ 5,01 mld) | 43,27% | **44,92%** |
| **alto − basso** | +0,36 pp (0,18 es) | **+4,54 pp (2,29 es)** |

**NQ monotono nella direzione del meccanismo, YM no.** E su NQ **nessun terzile supera il caso**
(~44%): non c'e' reversione sfruttabile nemmeno col gamma alto. Quello che cambia e' che **col
gamma basso il fade perde** di circa 4 punti contro il caso — cioe' li' il prezzo continua.

## Il paper per intero: Adams, Dim, Eraker, Fontaine, Ornthanalai, Vilkov (luglio 2026)

Unisce i due working paper (*0DTEs: Trading, Gamma Risk and Volatility Propagation* e il
lavoro sulla volatilita'). 75 pagine.

| | |
|---|---|
| campione | gennaio 2018 - dicembre 2024, futures E-mini e indice cash |
| gamma | netto dei market maker, **intraday**, ricostruito da **dati proprietari** sulle posizioni |
| orizzonte | reversione del flusso d'ordini significativa per **~30 minuti**, spenta entro l'ora; momentum misurato da 10 minuti a 2 ore |
| quartile basso di gamma | momentum **positivo**, fino a **~0,7 punti base** a 1-2 ore |
| quartile alto | momentum **negativo** (reversione) di **~1-2 punti base** |
| **differenza alto − basso** | **da −1 a −3 punti base**, significativa fra 30 minuti e 2 ore |

E gli autori lo dicono da soli (p. 33): *«this result does not translate into a feasible
trading strategy since the market makers' net gamma is not observable to other investors.»*

**Amaya, Garcia-Ares, Pearson, Vasquez** (2025): studia l'effetto sulla **volatilita'**, non sui
rendimenti, e usa dati proprietari Cboe. Non serve a una strategia.

## Verdetto: la direzione si chiude come fonte di strategie

Cade alla **domanda 9 del filtro**: *i dati che il segnale richiede sono accessibili a noi?* No.
Il segnale vero e' il gamma **intraday e proprietario**; il nostro proxy e' **giornaliero e
stimato**, e diluisce un effetto che vale 1-3 punti base — cioe' **$5-15 per micro** contro
$1,50 di costo, **prima** della diluizione.

## Ma resta, ed e' la cosa piu' utile di questa settimana: **spiega tutte le nostre morti**

| strategia | cosa e' successo | spiegazione |
|---|---|---|
| LastHalfHour | positiva nel 2022, negativa nel 2023-24 | momentum quando i dealer sono corti gamma, reversione quando sono lunghi; dal 2023 sono quasi sempre lunghi |
| VWAP fade, gap fade | zero su 2020-2024 | una mean reversion non condizionata mescola i due regimi e la media si annulla |
| il fade su NQ per terzili | perde col gamma basso, pareggia col gamma alto | stessa cosa, vista dall'altro lato |

## Una domanda che resta aperta, e riguarda la strategia viva

**DriftPullback e' momentum per la direzione.** Se il meccanismo e' giusto, dovrebbe rendere di
piu' nei giorni a gamma basso e di meno in quelli a gamma alto. Se fosse cosi', il GEX non
sarebbe un segnale ma un **indicatore di regime per dimensionare il rischio** di una strategia
che gia' funziona.

**Il vincolo di metodo**: l'OOS 2025-2026 di DriftPullback e' gia' stato usato. Un filtro
aggiunto adesso sarebbe una DriftPullback v2, validabile solo su dati nuovi — cioe' sul live.
Si puo' guardare la ripartizione per terzili sull'IS come **informazione sul rischio**, non come
modifica della strategia.
