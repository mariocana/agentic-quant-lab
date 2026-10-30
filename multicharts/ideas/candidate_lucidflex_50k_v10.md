<!-- researcher.py, 26/10/2026, claude-code on the claude.ai plan, model claude-opus-5-5, focus: TRIAGE, NON RICERCA. Lavora solo sulle fonti DA LEGGERE del database: non fare ricerche
web nuove. Per ciascuna decidi un verdetto e mettila in sources_reviewed:
- dal titolo, dall'URL e da cio' che sai, scarta subito quelle chiaramente fuori dai filtri
  del prompt (campione solo pre-2021 senza follow-up, azioni singole, opzioni, dati di book,
  overnight, crypto spot, teoria senza regola) e scrivi nel motivo "[titolo]";
- apri con WebFetch solo quelle che potrebbero passare, in ordine di promessa, fino al budget;
- quelle che restano promettenti ma non hai aperto: verdetto "aperto", motivo "da aprire".
Proponi una candidata solo se una fonte aperta la regge davvero. -->

# Ricerca seconda gamba — 26/10/2026 (solo triage delle fonti DA LEGGERE)

**Risultato: nessuna candidata e nessuna quasi-candidata.** Ho aperto 14 fonti su 15 consentite e non ho fatto ricerche web, come chiedeva l'indicazione. Delle 14, nessuna regge i filtri. Tre non si sono aperte (403 o verifica anti-bot). Le altre 108 fonti le ho giudicate dal titolo, dall'URL e da ciò che contiene già il database. Il risultato è negativo, come nelle ultime nove ricerche, ma il triage svuota quasi tutta la coda DA LEGGERE. Restano 3 fonti "aperto".

## Tabella di sintesi

| # | Nome | Fonte (paper / praticante) | Strumento · TF | Finestra oraria (CT) | Famiglia | Stop (punti) | trade/giorno | Eccesso o t dichiarato | Correlazione attesa con DriftPullback | Verdetto |
|---|---|---|---|---|---|---|---|---|---|---|
| — | nessuna | — | — | — | — | — | — | — | — | nessuna candidata passa i filtri |

## Le fonti che si avvicinavano, e perché non entrano

**1. YM intraday a cinque regole** (GitHub yukedizou-maker), livello 2. Ha dati dichiarati, costi dichiarati e nessun OOS.
- **Perché era interessante:** opera nell'ora libera. Ingresso alle 09:30 o 09:45 ET, cioè 08:30-08:45 CT, e uscita entro le 10:30 ET, cioè 09:30 CT. I segnali sono il rendimento overnight e quello della sessione europea (esempio S1: long se ov_ret ≤ −0,29% e Europa ≥ +0,14%) [fonte: README](https://github.com/yukedizou-maker/ym-intraday-quant-strategy-free-awesome).
- **Cosa dichiara:** 406 trade dal 2011 al 2026, WR 59,85%, PF 2,29, commissione $2,50 per lato più 1 punto di slippage per lato [fonte].
- **Perché la scarto:** sfora tre filtri.
  - **Frequenza:** 406 trade in circa 15 anni sono circa 27 l'anno [stima: 406/15], cioè circa 0,11 trade al giorno [stima: 27/252] contro un minimo di 0,4.
  - **P5:** non c'è stop, le uscite sono solo a tempo [fonte].
  - **P3:** il README dice che non c'è un periodo out-of-sample indipendente e non documenta come sono state scelte le regole [fonte].
- **Inoltre:** il motore del backtest non è nel repository (quindi anche P1 è dubbio), e cinque regole a soglia su 406 trade fanno pensare a regole cercate sui dati. Il segnale overnight più Europa, letto come rendimento relativo, ricorda anche la famiglia ON_Reversal, che è morta (t −2,24).

**2. Quantitativo, Intraday Momentum per ES e NQ.** È una replica della Noise Area di Zarattini, Aziz e Barbon, livello 2.
- **Cosa dichiara:** WR 36-39%, payoff circa 2,1, circa +6 bp per trade su NQ dopo i costi, dati dal 2010 al gennaio 2025, nessun OOS e nessun dettaglio sugli anni dopo il 2021 [fonte](https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq).
- **Perché la scarto:** la famiglia Noise Area è già scartata nel database, anche con una replica che ne mostra il degrado fuori campione ([ssrn:7290621](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7290621)). Inoltre è un trend following su tutta la seduta NQ: la correlazione con DriftPullback sarebbe alta per costruzione. Non porta nessun dato nuovo.

**3. Ritiro di liquidità prima degli annunci macro programmati** (Economics Letters, 2026). Ho ricevuto 403 e non l'ho letta, quindi resta "aperto".
- **Perché va riaperta:** è l'unica fonte recente sulla finestra delle 08:30 CT, che è l'idea "evento macro" già sul board in ricerca_18-10.
- **Il limite che so già:** quella famiglia fa circa 2-3 eventi a settimana. Da sola, quindi, rischia di stare sotto 0,4 trade al giorno [stima: 2,5/5 = 0,5 nel caso migliore, solo se ogni rilascio produce un trade].

## Scartate da me

| Idea | Fonte (link) | Motivo dello scarto in una riga |
|---|---|---|
| YM a cinque regole su overnight ed Europa | https://github.com/yukedizou-maker/ym-intraday-quant-strategy-free-awesome | 0,11 trade/giorno [stima], nessuno stop, nessun OOS (P3 e P5); motore non pubblicato |
| Noise Area su ES/NQ (replica) | https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq | Famiglia già scartata; trend su tutta la seduta, sovrapposto a DriftPullback; nessun dato post-2021 separato |
| Forward test "Automated Trading Strategies" Q2 2025 | https://automatedtradingstrategies.substack.com/p/q2-2025-forward-test-results | Paywall; conti simulati, in parte discrezionali; nessuna regola, costo o stop |
| Micro Pullback Entry System | https://cn.tradingview.com/script/K0f6aI3t-Micro-Pullback-Entry-System | Indicatore senza backtest, pensato per azioni in gap, stop al minimo del pullback |
| NQ Hourly Retracements 12y | https://de.tradingview.com/script/oJunuDml-NQ-Hourly-Retracements-12y-Stats-with-Levels | Statistiche di tocco senza regola, stop o backtest |
| YM "market maker cycles" (FOMC_God) | https://www.tradingview.com/chart/YM1!/FxdQNRZw-Full-Breakdown-of-My-Trading-Strategy-Dow-Futures-Daytrading/ | Discrezionale per ammissione dell'autore; nessuna statistica |
| Market Movement After Open | https://jp.tradingview.com/script/J0WtR2XF | Indicatore visivo, nessuna regola |
| Strategia Python su NQ (intro) | https://de.tradingview.com/chart/NQ1%21/4reovOWt-Intro-to-my-python-tradingview-strategy | Nessuna regola né risultato; l'autore dichiara che la prima versione era sovrattata |
| Toolkit MNQ walk-forward | https://github.com/fistu4088/mnq-backtest-toolkit | Stesso autore del post dev.to già scartato; dati Yahoo di 2 anni; nessun risultato |
| Interpretable Systematic Risk around the Clock | https://arxiv.org/pdf/2604.13458 | Portafoglio fattoriale ribilanciato ogni anno, non una regola intraday su futures |
| Le altre ~100 fonti | vedi il JSON | Scartate dal titolo: overnight drift, FX fix, opzioni, azioni singole, teoria, specifiche CME, duplicati |

## Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| Coda DA LEGGERE (122 voci), nessuna query nuova | 14 aperte, nessuna candidata | No: la coda è svuotata, tranne 3 voci "aperto" |
| Repository e script su GitHub e TradingView | Indicatori senza test, un repository YM con segnale nell'ora libera ma frequenza bassissima | Solo se un repository pubblica regole con stop e OOS |
| quantifiedstrategies.com (MES, M2K) | Bloccato dalla verifica anti-bot | Solo con un altro accesso; prior basso (di solito regole EOD) |
| sciencedirect S0165176526004520 | 403 | Sì: è l'unica fonte nuova sulle 08:30 CT |

**Osservazione sul processo, non sui criteri.** Circa due terzi della coda DA LEGGERE sono duplicati o pagine accessorie di fonti già scartate (overnight drift, FX fix, order-splitting) oppure specifiche CME. Il programma che riempie il database potrebbe saltare in automatico gli URL che puntano allo stesso lavoro di una fonte scartata. Nessuna pagina aperta conteneva istruzioni rivolte ad agenti.

```json
{"candidates": [],
"sources_reviewed": [
{"url":"https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq","title":"Intraday Momentum for ES and NQ - Quantitativo","kind":"site","verdict":"scartato","reason":"Replica Noise Area (famiglia scartata), WR 36-39%, nessun OOS né dettaglio post-2021, sovrapposta a DriftPullback","candidate":null},
{"url":"https://automatedtradingstrategies.substack.com/p/q2-2025-forward-test-results","title":"Automated Trading Strategies Q2 2025 forward test results","kind":"site","verdict":"scartato","reason":"Paywall; conti simulati in parte discrezionali, nessuna regola, costo o stop","candidate":null},
{"url":"https://automatedtradingstrategies.substack.com/p/breaking-q2-forward-test-launch","title":"Automated Trading Strategies Q2 forward test launch","kind":"site","verdict":"scartato","reason":"[titolo] annuncio della stessa serie paywalled, risultati già visti nella pagina Q2 results","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/pii/S0165176526004520","title":"Liquidity withdrawal before scheduled macroeconomic announcements","kind":"paper","verdict":"aperto","reason":"403 al fetch; unica fonte recente sulla finestra 08:30 CT, da aprire con altro accesso","candidate":null},
{"url":"https://github.com/yukedizou-maker/ym-intraday-quant-strategy-free-awesome","title":"YM intraday quant strategy (5 regole)","kind":"site","verdict":"scartato","reason":"406 trade in 15 anni ≈0,11/giorno, nessuno stop, nessun OOS, motore non pubblicato","candidate":null},
{"url":"https://cn.tradingview.com/script/K0f6aI3t-Micro-Pullback-Entry-System","title":"Micro Pullback Entry System","kind":"site","verdict":"scartato","reason":"Indicatore senza backtest, per azioni in gap","candidate":null},
{"url":"https://kr.tradingview.com/script/K0f6aI3t-Micro-Pullback-Entry-System","title":"Micro Pullback Entry System (kr)","kind":"site","verdict":"scartato","reason":"Duplicato della versione cn, indicatore senza test","candidate":null},
{"url":"https://my.tradingview.com/script/K0f6aI3t-Micro-Pullback-Entry-System","title":"Micro Pullback Entry System (my)","kind":"site","verdict":"scartato","reason":"Duplicato, indicatore senza test","candidate":null},
{"url":"https://vn.tradingview.com/script/K0f6aI3t-Micro-Pullback-Entry-System","title":"Micro Pullback Entry System (vn)","kind":"site","verdict":"scartato","reason":"Duplicato, indicatore senza test","candidate":null},
{"url":"https://www.quantifiedstrategies.com/micro-e-mini-russell-trading-strategy/","title":"Micro E-mini Russell Trading Strategy - QuantifiedStrategies","kind":"site","verdict":"scartato","reason":"Bloccata da verifica anti-bot; [titolo] il sito pubblica di solito regole EOD/multi-day","candidate":null},
{"url":"https://www.quantifiedstrategies.com/micro-e-mini-sp-500-index-trading-strategy/","title":"Micro E-mini S&P 500 Trading Strategy - QuantifiedStrategies","kind":"site","verdict":"scartato","reason":"Bloccata da verifica anti-bot; [titolo] il sito pubblica di solito regole EOD/multi-day","candidate":null},
{"url":"https://www.quantifiedstrategies.com/opening-range-breakout-strategy/","title":"Opening Range Breakout Strategy (ORB) - QuantifiedStrategies","kind":"site","verdict":"scartato","reason":"[titolo] famiglia ORB già morta tre volte nei nostri test","candidate":null},
{"url":"https://de.tradingview.com/script/oJunuDml-NQ-Hourly-Retracements-12y-Stats-with-Levels","title":"NQ Hourly Retracements - 12y Stats with Levels","kind":"site","verdict":"scartato","reason":"Statistiche di tocco senza regola, stop o backtest","candidate":null},
{"url":"https://in.tradingview.com/scripts/search/%E5%BE%AE%E8%BD%AF%E8%82%A1%E6%81%AF%E6%94%AF%E4%BB%98%E7%8E%872025%E6%9C%80%E6%96%B0%E6%95%B0%E6%8D%AE/page-4","title":"NQ Hourly Retracements (pagina di ricerca TradingView)","kind":"site","verdict":"scartato","reason":"Duplicato dello script NQ Hourly Retracements, senza regola","candidate":null},
{"url":"https://www.tradingview.com/chart/YM1!/FxdQNRZw-Full-Breakdown-of-My-Trading-Strategy-Dow-Futures-Daytrading/","title":"Full Breakdown of My Trading Strategy Dow Futures (FOMC_God)","kind":"forum","verdict":"scartato","reason":"Discrezionale per ammissione dell'autore, nessuna statistica","candidate":null},
{"url":"https://jp.tradingview.com/script/J0WtR2XF","title":"Market Movement After Open (base751)","kind":"site","verdict":"scartato","reason":"Indicatore visivo, nessuna regola né test","candidate":null},
{"url":"https://de.tradingview.com/chart/NQ1%21/4reovOWt-Intro-to-my-python-tradingview-strategy","title":"Intro to my python tradingview strategy (NQ)","kind":"forum","verdict":"scartato","reason":"Nessuna regola né risultato pubblicato","candidate":null},
{"url":"https://github.com/fistu4088/mnq-backtest-toolkit","title":"mnq-backtest-toolkit","kind":"site","verdict":"scartato","reason":"Stesso autore del dev.to scartato; dati Yahoo di 2 anni, nessun risultato per strategia","candidate":null},
{"url":"https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4718961","title":"Can Daily Closing Prices Predict Future Movements? Limit Order Clustering","kind":"paper","verdict":"scartato","reason":"403; [titolo] orizzonte da chiusura a giorni successivi, azioni: fallisce i filtri 1 e 5","candidate":null},
{"url":"https://arxiv.org/pdf/2604.13458","title":"Interpretable Systematic Risk around the Clock","kind":"paper","verdict":"scartato","reason":"Portafoglio fattoriale ribilanciato annualmente, nessuna regola intraday su futures","candidate":null},
{"url":"https://alphaarchitect.com/?p=57408","title":"Market Return Around the Clock: A Puzzle","kind":"site","verdict":"scartato","reason":"[titolo] duplicato della pagina Alpha Architect già scartata (filtro 8)","candidate":null},
{"url":"https://cepr.org/publications/dp14462","title":"CEPR DP14462","kind":"paper","verdict":"aperto","reason":"da aprire: titolo non informativo, contenuto ignoto","candidate":null},
{"url":"https://www.cmegroup.com/education/frequently-asked-questions-micro-e-mini-equity-index-futures.html","title":"FAQ Micro E-mini Equity Index Futures","kind":"other","verdict":"scartato","reason":"[titolo] specifica di contratto, non strategia","candidate":null},
{"url":"https://cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.options.html","title":"Micro E-mini S&P 500 contract specs (options)","kind":"other","verdict":"scartato","reason":"[titolo] specifica, non strategia","candidate":null},
{"url":"https://www.cmegroup.com/notices/ser/2019/04/SER-8360.pdf","title":"CME SER 8360","kind":"other","verdict":"scartato","reason":"[titolo] avviso regolamentare 2019, non strategia","candidate":null},
{"url":"https://cmegroup.com/trading/equity-index/us-index/micro-e-mini-sandp-500_contract_specifications.html","title":"Micro E-mini S&P 500 contract specifications","kind":"other","verdict":"scartato","reason":"[titolo] specifica, non strategia","candidate":null},
{"url":"https://www.dii.uchile.cl/?p=99939","title":"www.dii.uchile.cl","kind":"other","verdict":"scartato","reason":"[titolo] pagina di dipartimento senza indizio di strategia","candidate":null},
{"url":"https://econpapers.repec.org/RePEc:fip:fednls:103479","title":"The Disappearing Overnight Drift (EconPapers)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato; overnight drift morto dopo il 2021 (filtro 8)","candidate":null},
{"url":"https://www.fedinprint.org/item/fednls/103479","title":"The Disappearing Overnight Drift (FedInPrint)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, overnight, filtro 8","candidate":null},
{"url":"https://fedinprint.org/item/fednls/92064","title":"fedinprint 92064","kind":"paper","verdict":"scartato","reason":"[titolo] serie Liberty Street sull'overnight drift, overnight e pre-2021","candidate":null},
{"url":"https://ideas.repec.org/f/c/pbo573.html","title":"Nina Boyarchenko (pagina autore)","kind":"other","verdict":"scartato","reason":"[titolo] pagina autore, overnight drift già chiuso","candidate":null},
{"url":"https://ideas.repec.org/p/fip/fednls/103479.html","title":"The Disappearing Overnight Drift (IDEAS)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, filtro 8","candidate":null},
{"url":"https://ideas.repec.org/p/fip/fednls/92064.html","title":"IDEAS fednls 92064","kind":"paper","verdict":"scartato","reason":"[titolo] serie overnight drift, overnight","candidate":null},
{"url":"https://ideas.repec.org/s/fip/fednls.html","title":"Liberty Street Economics (serie IDEAS)","kind":"other","verdict":"scartato","reason":"[titolo] indice di serie, non fonte","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/tag/overnight-drift","title":"Liberty Street tag overnight-drift","kind":"site","verdict":"scartato","reason":"[titolo] overnight drift, morto per gli autori","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/tag/paul-whelan/","title":"The Overnight Drift in U.S. Equity Returns (tag)","kind":"site","verdict":"scartato","reason":"[titolo] overnight, filtro 8","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/tag/sp-500/","title":"The Overnight Drift in U.S. Equity Returns (tag sp-500)","kind":"site","verdict":"scartato","reason":"[titolo] overnight, filtro 8","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/tag/us-equity-returns/","title":"Liberty Street tag us-equity-returns","kind":"site","verdict":"scartato","reason":"[titolo] overnight, filtro 8","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/?p=40","title":"Liberty Street Economics ?p=40","kind":"site","verdict":"scartato","reason":"[titolo] pagina generica del blog","candidate":null},
{"url":"https://libertystreeteconomics.newyorkfed.org/?p=43261","title":"Liberty Street Economics ?p=43261","kind":"site","verdict":"scartato","reason":"[titolo] probabile post overnight drift, già chiuso","candidate":null},
{"url":"https://research.cbs.dk/da/publications/the-overnight-drift-in-us-equity-returns/","title":"The Overnight Drift in US Equity Returns (CBS)","kind":"paper","verdict":"scartato","reason":"[titolo] overnight, filtro 8","candidate":null},
{"url":"https://research.cbs.dk/en/publications/the-overnight-drift-4/","title":"The Overnight Drift (CBS)","kind":"paper","verdict":"scartato","reason":"[titolo] overnight, filtro 8","candidate":null},
{"url":"https://tradestation.com/?p=53952","title":"TradeStation ?p=53952","kind":"vendor","verdict":"scartato","reason":"[titolo] pagina di broker senza titolo informativo","candidate":null},
{"url":"https://www.academia.edu/7986665/E_mini_S_and_P_500_Futures_Order_Placement_and_Trading_Costs","title":"E-mini S&P 500 Futures Order Placement and Trading Costs","kind":"paper","verdict":"scartato","reason":"[titolo] microstruttura dei costi, nessuna regola di segnale","candidate":null},
{"url":"https://academicweb.nd.edu/~zda/IntraOption.pdf","title":"Intraday Option Return Predictability","kind":"paper","verdict":"scartato","reason":"[titolo] opzioni, dati che non abbiamo","candidate":null},
{"url":"https://www.aeaweb.org/conference/2020/preliminary/paper/2dedYfDH","title":"Foreign Exchange Fixings and Returns Around the Clock (AEA)","kind":"paper","verdict":"scartato","reason":"[titolo] FX Fix già testata e morta (t -1,1/-0,41)","candidate":null},
{"url":"https://ageconsearch.umn.edu/record/19011/files/cp04pa01.pdf","title":"The Profitability of Technical Trading Rules in US Futures","kind":"paper","verdict":"scartato","reason":"[titolo] regole giornaliere, campione vecchio (filtri 5, 8)","candidate":null},
{"url":"https://ageconsearch.umn.edu/record/37487/files/AgMAS04_04.pdf","title":"The Profitability of Technical Analysis","kind":"paper","verdict":"scartato","reason":"[titolo] survey del 2004, nessuna regola intraday","candidate":null},
{"url":"https://amanda.ece.utah.edu/2026/10/17/s-p-500-futures-indicators-reports-and-risk-control-i1710a7/","title":"S & P 500 Futures: Indicators, Reports and Risk Control","kind":"other","verdict":"scartato","reason":"[titolo] contenuto generico su dominio universitario anomalo, probabile spam","candidate":null},
{"url":"https://ar.tradingview.com/chart/M2KU2022/k0b6Xgoy-M2K-Micro-E-mini-Future-Russell-2000","title":"M2K Micro E-mini Future Russell 2000 (idea)","kind":"forum","verdict":"scartato","reason":"[titolo] idea discrezionale del 2022","candidate":null},
{"url":"https://it.tradingview.com/chart/M2KU2022/k0b6Xgoy-M2K-Micro-E-mini-Future-Russell-2000","title":"M2K Micro E-mini Future Russell 2000 (idea, it)","kind":"forum","verdict":"scartato","reason":"[titolo] duplicato, idea discrezionale","candidate":null},
{"url":"https://ar.tradingview.com/script/5N3VYOCF-Previous-Day-Sweep","title":"Previous Day Sweep","kind":"site","verdict":"scartato","reason":"[titolo] script di reversal senza test; query prior-day sweep già fatta","candidate":null},
{"url":"https://de.tradingview.com/script/3M56QPhj-Liquidity-Sweep-Reversal-Grimoire","title":"Liquidity Sweep Reversal Grimoire","kind":"site","verdict":"scartato","reason":"[titolo] script mean reversion senza test","candidate":null},
{"url":"http://arno.uvt.nl/show.cgi?fid=144554","title":"Intraday Price Reversals and Momentum: Evidence from the NYSE","kind":"paper","verdict":"scartato","reason":"[titolo] azioni NYSE, tesi (filtro 1)","candidate":null},
{"url":"https://arxiv.org/pdf/cond-mat/0312658","title":"Causal Slaving of the U.S. Treasury Bond Yield Antibubble","kind":"paper","verdict":"scartato","reason":"[titolo] macro 2000, nessuna regola intraday","candidate":null},
{"url":"https://arxiv.org/pdf/cond-mat/0406696","title":"Short-term market reaction after extreme price changes of liquid stocks","kind":"paper","verdict":"scartato","reason":"[titolo] azioni singole, campione vecchio","candidate":null},
{"url":"https://arxiv.org/pdf/1005.3535","title":"Intraday Patterns in the Cross-section of Stock Returns","kind":"paper","verdict":"scartato","reason":"[titolo] cross-section azionario","candidate":null},
{"url":"https://arxiv.org/pdf/1102.2138","title":"The US stock market leads the Federal funds rate and Treasury bond yields","kind":"paper","verdict":"scartato","reason":"[titolo] macro, non intraday","candidate":null},
{"url":"https://arxiv.org/pdf/1212.0479","title":"Modeling non-stationarities in high-frequency financial time series","kind":"paper","verdict":"scartato","reason":"[titolo] modellistica senza regola","candidate":null},
{"url":"https://arxiv.org/pdf/1504.06235","title":"Lead-Lag Relationship using a Stop-and-Reverse-MinMax Process","kind":"paper","verdict":"scartato","reason":"[titolo] metodo statistico, lead-lag fra indici correlati","candidate":null},
{"url":"https://arxiv.org/pdf/1601.04210","title":"Speculative Futures Trading under Mean Reversion","kind":"paper","verdict":"scartato","reason":"[titolo] teoria di stopping ottimo, mean reversion","candidate":null},
{"url":"https://arxiv.org/pdf/1605.07945","title":"Trading VIX Futures under Mean Reversion with Regime Switching","kind":"paper","verdict":"scartato","reason":"[titolo] VX non CME, teoria","candidate":null},
{"url":"https://arxiv.org/pdf/1611.03110","title":"Asynchronous ADRs: Overnight vs Intraday Returns","kind":"paper","verdict":"scartato","reason":"[titolo] ADR azionari, overnight","candidate":null},
{"url":"https://arxiv.org/pdf/1612.01232","title":"Wavelet-based methods for high-frequency lead-lag analysis","kind":"paper","verdict":"scartato","reason":"[titolo] metodo, nessuna regola","candidate":null},
{"url":"https://arxiv.org/pdf/1712.07649","title":"Trading Strategies with Position Limits","kind":"paper","verdict":"scartato","reason":"[titolo] teoria","candidate":null},
{"url":"https://arxiv.org/pdf/2004.01624","title":"How to build a cross-impact model from first principles","kind":"paper","verdict":"scartato","reason":"[titolo] modello di impatto, nessuna regola","candidate":null},
{"url":"https://arxiv.org/pdf/2011.04367","title":"Comparing the market microstructure between two South African exchanges","kind":"paper","verdict":"scartato","reason":"[titolo] mercati sudafricani","candidate":null},
{"url":"https://arxiv.org/pdf/2206.13138","title":"High-Frequency Causality in the VIX Index and its derivatives","kind":"paper","verdict":"scartato","reason":"[titolo] VIX/derivati, nessuna regola","candidate":null},
{"url":"https://arxiv.org/pdf/2302.10175","title":"Spatio-Temporal Momentum","kind":"paper","verdict":"scartato","reason":"[titolo] ML, frequenza giornaliera","candidate":null},
{"url":"https://arxiv.org/pdf/2401.10722","title":"Stylized Facts and Market Microstructure: German Bond Futures","kind":"paper","verdict":"scartato","reason":"[titolo] Eurex, non disponibile","candidate":null},
{"url":"https://arxiv.org/pdf/2501.03171","title":"High-frequency lead-lag in the Chinese stock index futures market","kind":"paper","verdict":"scartato","reason":"[titolo] futures cinesi, tick data","candidate":null},
{"url":"https://arxiv.org/pdf/2602.10711","title":"Cross-Sectional Asset Retrieval via Future-Aligned Soft Contrastive Learning","kind":"paper","verdict":"scartato","reason":"[titolo] ML cross-section","candidate":null},
{"url":"https://arxiv.org/pdf/2605.11423","title":"A Validated Volatility-Volume-Gap Classifier for MNQ","kind":"paper","verdict":"scartato","reason":"[titolo] classificatore VVG già scartato nel db","candidate":null},
{"url":"https://arxiv.org/pdf/2608.21888","title":"Short-horizon mean reversion in cryptocurrency markets","kind":"paper","verdict":"scartato","reason":"[titolo] crypto, mean reversion; già usato in ricerca_18-10","candidate":null},
{"url":"https://arxiv.org/pdf/2609.05905","title":"From Narrative to Auditable Forecasts: agentic forecasting","kind":"paper","verdict":"scartato","reason":"[titolo] previsioni con LLM, non codificabile","candidate":null},
{"url":"https://www.bis.org/events/221213_bis_bdi_ecb_exchange_rates/mueller.pdf","title":"BIS Mueller (FX fixings)","kind":"paper","verdict":"scartato","reason":"[titolo] FX Fix già testata e morta","candidate":null},
{"url":"https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf","title":"Intraday Momentum: first half-hour predicts last half-hour","kind":"paper","verdict":"scartato","reason":"[titolo] Gao et al., famiglia LastHalfHour morta","candidate":null},
{"url":"https://www.cftc.gov/sites/default/files/Stoploss_final_ada.pdf","title":"Stop Orders in Select Futures Markets (CFTC)","kind":"paper","verdict":"scartato","reason":"[titolo] studio descrittivo, nessuna regola","candidate":null},
{"url":"https://pubsonline.informs.org/doi/10.1287/opre.13.2.258","title":"Clustering of Stock Prices (1965)","kind":"paper","verdict":"scartato","reason":"[titolo] 1965, azioni","candidate":null},
{"url":"https://www.efmaefm.org/0efmameetings/efma%20annual%20meetings/2009-Milan/papers/719.pdf","title":"Round Numbers and Security Returns","kind":"paper","verdict":"scartato","reason":"[titolo] azioni, 2009, filtro 8","candidate":null},
{"url":"https://en.saif.sjtu.edu.cn/junpan/PreAnn_20210728.pdf","title":"Premium for Heightened Uncertainty (Hu-Pan-Wang-Zhu)","kind":"paper","verdict":"scartato","reason":"[titolo] già scartato nel db: overnight, premio al rischio","candidate":null},
{"url":"https://eprints.soton.ac.uk/452387/1/PhD_thesis.pdf","title":"Essays on Intraday Stock Return Predictability","kind":"paper","verdict":"scartato","reason":"[titolo] azioni, tesi","candidate":null},
{"url":"https://faculty.haas.berkeley.edu/hender/liq_provision_ret_predict_JBF.pdf","title":"Liquidity provision and stock return predictability","kind":"paper","verdict":"scartato","reason":"[titolo] azioni singole, dati di flusso","candidate":null},
{"url":"https://github.com/CommunityPokeOrg/index-futures-stat-arb/issues/1","title":"index-futures-stat-arb issue #1","kind":"site","verdict":"scartato","reason":"[titolo] issue di repository già scartato","candidate":null},
{"url":"https://github.com/ikeawesom/xauusd-backtest","title":"xauusd-backtest","kind":"site","verdict":"scartato","reason":"[titolo] oro spot, strategia sweep; famiglia MGC già chiusa","candidate":null},
{"url":"https://ideas.repec.org/r/eee/jbfina/v25y2001i8p1543-1551.html","title":"IDEAS bibliografia JBF 2001","kind":"other","verdict":"scartato","reason":"[titolo] pagina di citazioni di un paper del 2001","candidate":null},
{"url":"https://ies.keio.ac.jp/upload/20190716macro_Martineau_abstract-1.pdf","title":"Price Pressure and Efficiency on FOMC Announcements","kind":"paper","verdict":"scartato","reason":"[titolo] 8 eventi l'anno, sotto la frequenza minima","candidate":null},
{"url":"https://ink.library.smu.edu.sg/context/lkcsb_research/article/7402/viewcontent/____Intraday_information_from_S_P_500_Index_Futures_Options.pdf","title":"Intraday information from S&P 500 Index futures options","kind":"paper","verdict":"scartato","reason":"[titolo] richiede dati di opzioni","candidate":null},
{"url":"https://www.researchgate.net/publication/328209193_Intraday_information_from_SP_500_Index_futures_options","title":"Intraday information from S&P 500 Index futures options (RG)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, opzioni","candidate":null},
{"url":"https://www.nber.org/system/files/working_papers/w23327/w23327.pdf","title":"Did the Reform Fix the London Fix Problem?","kind":"paper","verdict":"scartato","reason":"[titolo] FX fix e manipolazione, già chiusa","candidate":null},
{"url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3154254/","title":"The US Stock Market Leads the Federal Funds Rate","kind":"paper","verdict":"scartato","reason":"[titolo] macro, non intraday","candidate":null},
{"url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5094667/","title":"Intraday Seasonalities and Nonstationarity of Trading Volume","kind":"paper","verdict":"scartato","reason":"[titolo] volumi, nessuna regola","candidate":null},
{"url":"https://nexusfi.com/a/strategies/opening-range-breakout","title":"Opening Range Breakout - NexusFi Academy","kind":"site","verdict":"scartato","reason":"[titolo] ORB, famiglia morta","candidate":null},
{"url":"https://nsd.pku.edu.cn/docs/20230206095723035155.pdf","title":"Option Pricing with Overnight and Intraday Volatility","kind":"paper","verdict":"scartato","reason":"[titolo] pricing di opzioni","candidate":null},
{"url":"https://pages.nes.ru/aobizhaeva/ABKO-intradayinv.pdf","title":"Intraday Trading Invariance in the E-mini S&P 500","kind":"paper","verdict":"scartato","reason":"[titolo] microstruttura teorica, nessuna regola","candidate":null},
{"url":"https://www.researchgate.net/publication/314514151_Intraday_Trading_Invariance_in_the_E-Mini_SP_500_Futures_Market","title":"Intraday Trading Invariance (RG)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, nessuna regola","candidate":null},
{"url":"https://pages.stern.nyu.edu/~jh4/SternMicroMtg/Old/SternMicroMtg2015/Papers/Preannouncement_042015Strasser.pdf","title":"Price Drift before U.S. Macroeconomic News","kind":"paper","verdict":"scartato","reason":"[titolo] famiglia drift pre-annuncio già scartata, campione fino al 2014","candidate":null},
{"url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC9107071","title":"Multi-market Comparison of Intraday Lead-Lag among Spot, Futures and Options","kind":"paper","verdict":"scartato","reason":"[titolo] lead-lag descrittivo, nessuna regola","candidate":null},
{"url":"https://research.cbs.dk/en/publications/foreign-exchange-fixings-and-returns-around-the-clock/","title":"Foreign Exchange Fixings and Returns Around the Clock (CBS)","kind":"paper","verdict":"scartato","reason":"[titolo] FX Fix già testata e morta","candidate":null},
{"url":"https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802","title":"Foreign Exchange Fixings and Returns Around the Clock (INSEAD)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato FX Fix","candidate":null},
{"url":"https://www.researchgate.net/publication/222520781_Intraday_price_reversals_in_the_US_stock_index_futures_market_A_15-year_study","title":"Intraday price reversals in US stock index futures (Grant-Wolf-Yu)","kind":"paper","verdict":"scartato","reason":"[titolo] già scartato nel db, campione fino al 2002","candidate":null},
{"url":"https://scispace.com/pdf/intraday-price-reversals-for-index-futures-in-the-us-and-137ieyy6y7.pdf","title":"Intraday price reversals for index futures in the US and Hong Kong","kind":"paper","verdict":"scartato","reason":"[titolo] famiglia Grant-Wolf-Yu, mean reversion vecchia","candidate":null},
{"url":"https://www.researchgate.net/publication/242770982_Intraday_Trading_Volume_Patterns_Of_Equity_Markets_A_Study_Of_US_And_European_Stock_Markets","title":"Intraday Trading Volume Patterns of Equity Markets","kind":"paper","verdict":"scartato","reason":"[titolo] volumi, nessuna regola","candidate":null},
{"url":"https://www.researchgate.net/publication/348655910_Intraday_time_series_momentum_global_evidence_and_links_to_market_characteristics","title":"Intraday time series momentum: Global evidence","kind":"paper","verdict":"scartato","reason":"[titolo] versione centaur già scartata, famiglia LastHalfHour","candidate":null},
{"url":"http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf","title":"Intraday Time Series Momentum: International Evidence","kind":"paper","verdict":"scartato","reason":"[titolo] famiglia LastHalfHour, campione pre-2020 (filtro 8)","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S0264999321000134","title":"Intraday return predictability in China's crude oil futures","kind":"paper","verdict":"scartato","reason":"[titolo] futures cinesi","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351","title":"Market intraday momentum (Gao et al.)","kind":"paper","verdict":"scartato","reason":"[titolo] già scartato, famiglia LastHalfHour","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S0378437119318539","title":"Market liquidity and macro announcement around intraday jumps: Chinese futures","kind":"paper","verdict":"scartato","reason":"[titolo] futures cinesi","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S105905601200072X","title":"Predictability of opening returns: Taiwan futures","kind":"paper","verdict":"scartato","reason":"[titolo] Taiwan, campione pre-2012","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S1544612319304337","title":"Intraday time-series momentum in Chinese stock index futures","kind":"paper","verdict":"scartato","reason":"[titolo] futures cinesi, famiglia LastHalfHour","candidate":null},
{"url":"https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6087107","title":"Regime-Conditioned Mean Reversion Framework for Intraday FX","kind":"paper","verdict":"scartato","reason":"[titolo] FX spot e mean reversion autonoma","candidate":null},
{"url":"https://tradingstats.net/mean-reversion-trading-strategy/","title":"Mean Reversion Trading Strategy: 565 Weeks of NQ Data","kind":"site","verdict":"scartato","reason":"[titolo] mean reversion autonoma, esclusa per famiglia","candidate":null},
{"url":"https://www.tradingview.com/symbols/CBOT_MINI-MYM1!/ideas/?sort=recent&video=yes","title":"MYM Trade Ideas — TradingView","kind":"forum","verdict":"scartato","reason":"[titolo] feed di idee discrezionali","candidate":null},
{"url":"https://www.tradingview.com/symbols/CBOT_MINI-YM1!/ideas/","title":"YM Trade Ideas — TradingView","kind":"forum","verdict":"scartato","reason":"[titolo] feed di idee discrezionali","candidate":null},
{"url":"https://www.tradingview.com/symbols/CME_MINI-M2K1!/","title":"M2K price chart — TradingView","kind":"other","verdict":"scartato","reason":"[titolo] pagina di quotazione","candidate":null},
{"url":"https://arxiv.org/html/2105.13401","title":"arxiv 2105.13401 (1Introduction)","kind":"paper","verdict":"aperto","reason":"da aprire: titolo non estratto, contenuto ignoto","candidate":null},
{"url":"https://arxiv.org/pdf/2206.08117","title":"Trading constraints in continuous-time Kyle models","kind":"paper","verdict":"scartato","reason":"[titolo] teoria","candidate":null},
{"url":"https://arxiv.org/pdf/2504.10282","title":"Optimal Execution in Intraday Energy Markets under Hawkes Processes","kind":"paper","verdict":"scartato","reason":"[titolo] esecuzione su energia europea, teoria","candidate":null},
{"url":"https://link.springer.com/article/10.1007/s11579-020-00278-7","title":"Equilibrium effects of intraday order-splitting benchmarks (Springer)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato di arXiv 1803.08336 già scartato","candidate":null},
{"url":"https://www.researchgate.net/publication/386959248_Equilibrium_Effects_of_Intraday_Order-Splitting_Benchmarks","title":"Equilibrium Effects of Intraday Order-Splitting Benchmarks (RG)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, teoria","candidate":null},
{"url":"https://www.researchwithrutgers.com/en/publications/equilibrium-effects-of-intraday-order-splitting-benchmarks/","title":"Equilibrium effects of intraday order-splitting benchmarks (Rutgers)","kind":"paper","verdict":"scartato","reason":"[titolo] duplicato, teoria","candidate":null},
{"url":"https://www.sciencedirect.com/science/article/abs/pii/S0304405X18303118","title":"Information and trading targets in a dynamic market equilibrium","kind":"paper","verdict":"scartato","reason":"[titolo] teoria di equilibrio","candidate":null}
]}
```

---

## Gate 0 — verifica automatica (gate0.py, nessun modello)

Ricalcolato da codice, non dal ricercatore. `?` = numero non fornito. Filtri del prompt del 26/10/2026 (seconda gamba).

| Candidata | Fonte | Esito | Controlli |
|---|---|---|---|
| — | — | nessuna candidata | — |
