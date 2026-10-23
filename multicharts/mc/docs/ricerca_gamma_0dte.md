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
