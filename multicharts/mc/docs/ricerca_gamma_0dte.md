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
