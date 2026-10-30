<!-- researcher.py, 22/10/2026, model claude-sonnet-5-5, effort high -->

Comincio dalle fonti DA LEGGERE e da query nuove, che non ripetono quelle già fatte.
PDF in base64: lo decodifico ed estraggo il testo.
# Ricerca del 22/10/2026: nessuna candidata nuova, una pista aperta

**Esito.** Non consegno candidate e non consegno quasi-candidate. Il prompt prevede questo esito come legittimo. In questa ricerca ho trovato sette piste, e nessuna rispetta i vincoli. Una resta aperta perché non sono riuscito a leggere il paper.

**Limite di questa sessione.** Il limite di chiamate agli strumenti si è esaurito a metà lavoro. Non ho potuto leggere il paper di Boyarchenko-Larsen-Whelan, né le pagine M2K/MYM (specifiche e commissioni) tra le fonti DA LEGGERE. Restano da leggere.

**Come leggere le citazioni.** Ho letto per intero solo tre fonti: Krohn (Bank of Canada), la pagina Nasdaq sul MOC e la pagina sellside sul MOC. Le altre le ho giudicate dal titolo e dall'estratto restituito dalla ricerca, e nel testo lo dico. Non uso i tag di citazione perché gli indici delle fonti non erano disponibili in questo flusso. Metto i link.

## Tabella di sintesi

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| – | nessuna candidata | – | – | – | – | – | – | – | **vuoto** |
| (pista) | Overnight drift su E-mini, finestra Globex europea | MES/MNQ · 5 min | other | **[manca]** | ~250 [stima: 1 al giorno] | **[manca]** | **[manca]** | [MSU Broad](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/) (comunicato) | **aperta, da leggere** |

## Le piste valutate

Scheda di `come_scegliere_un_paper.md`: 1 = futures, 3 = flusso forzato, 5 = intraday e frequenza. Sono i tre filtri eliminatori.

| Pista | Fonte | 1 | 3 | 5 | Costi | Esito |
|---|---|---|---|---|---|---|
| **Fix FX 4pm Londra / Francoforte / Tokyo** (V-shape attorno al fix) | [Krohn et al., JF 2024, WP Bank of Canada](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf) | sì: il pattern c'è anche sui futures FX CME | sì: i dealer coprono pre-fix la domanda di dollari | sì, 1-3 segnali al giorno | gli autori scrivono che la maggior parte dei profitti sparisce con i costi | **scartata** |
| **FOMC announcement reversal** | [Baglioni-Ribeiro, feb. 2025](https://www.researchgate.net/publication/362775066_The_FOMC_Announcement_Reversal) | sì: E-mini S&P | no: eccesso di reazione pre-annuncio, non un flusso obbligato | sì: compra o vende alle 13:50 ET e chiude 2 ore dopo | prezzi bid/ask a 1 minuto | **scartata** |
| **Overnight drift** (finestra europea) | [MSU Broad](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/) e [arXiv 2507.04481 §5.4](https://arxiv.org/pdf/2507.04481) | sì | probabile: gestione dell'inventario degli intermediari | sì, 1 al giorno | **[manca]** | **aperta** |

### Fix FX

- **Ampiezza dell'effetto.** Gli autori misurano circa 2,5 punti base di apprezzamento del dollaro prima del fix e un deprezzamento della stessa entità dopo. I t-stat vanno da 4,5 a 11,7. È testato con dati, ma senza costi [fonte: Krohn et al.]. È un effetto vero e con un meccanismo forzato.
- **Aritmetica per micro (euro).** Il livello EUR/USD non è nelle fonti, quindi lo assumo a ~1,1 [stima]. I 2,5 punti base valgono 2,5 × 1,1 ≈ 2,75 pip. Prendo il valore del pip del micro euro a $1,25 [stima, da verificare su CME: contratto da 12.500 EUR, tick 0,0001]. Il lordo è circa $3,4 per trade per micro.
- **Confronto con la soglia.** Con un solo fix al giorno (Londra), il lordo è circa $3,4 al giorno per micro, contro la soglia di $10 [stima]. I costi lo riducono ancora. Il lordo da solo è già sotto la soglia di $10, quindi muore per la regola della frequenza e del $/giorno.
- **Profilo.** WR e R:R non sono riportati [manca]. Gli autori dicono che il segnale è piccolo e a basso edge per trade.
- **Un solo falsificatore, fatto prima.** Il lordo per trade deve superare 3 volte il costo andata-ritorno. Il lordo è circa $3,4 e il costo andata-ritorno del micro non lo conosco [manca]. Il test non vale la pena di un run.

### FOMC reversal

- **Frequenza.** Le riunioni programmate sono circa 8 all'anno [stima, conoscenza generale: non la leggo nella fonte]. Con circa 8 trade all'anno non si evita l'inattività e il $/giorno è zero.
- **Meccanismo.** Gli autori lo spiegano come eccesso di reazione. È un pattern comportamentale e non un flusso obbligato, quindi il filtro 3 lo elimina.
- **Fonte correlata.** [FEDS 2025-022](https://www.federalreserve.gov/econres/feds/files/2025022pap.pdf) parla di reversal dopo qualche giorno, quindi multi-day.

### Overnight drift: la pista aperta

- **Cosa dice la fonte.** Il comunicato MSU Broad riporta uno studio sugli E-mini S&P 2006-2018. Secondo il comunicato, il 100% del rendimento medio si concentra in una finestra di quattro ore, con rendimento in ogni anno. Con le festività europee il rendimento in quella finestra è vicino a zero [fonte, livello 2: è un comunicato, non il paper]. L'arXiv 2507.04481 §5.4 cita Boyarchenko-Larsen-Whelan (2023) e attribuisce il fenomeno all'inventario degli intermediari: sono compensati per aver assorbito gli squilibri della chiusura NYSE.
- **Attenzione all'orario.** Il comunicato indica 23:30-03:30, e dice che 23:30 corrisponde alle 4:30 tedesche. Questo non torna con ET: la differenza è di solito 6 ore, quindi 23:30 ET sarebbe le 5:30 tedesche. **Fuso e finestra esatta: [manca].**
- **Aritmetica minima per passare lo screening a 1 trade al giorno su MES.** Parto dal costo del micro di ~$3 andata-ritorno [stima: $30 dell'ES nel prompt, diviso 10]. Per fare $10 netti per micro al giorno servono circa $13 lordi, cioè 13/5 = 2,6 punti MES per notte.
- **Confronto col livello dell'indice.** Con l'S&P a circa 7.800 ([CNBC 05/10/2026](https://www.cnbc.com/2026/10/05/stock-market-today-live-updates.html)), 2,6/7.800 ≈ 3,3 punti base per notte [stima]. Il rendimento medio giornaliero totale dell'S&P non è nelle fonti [manca]. Se fosse intorno a 4 punti base (~10% annuo diviso 252, ipotesi mia), il margine sarebbe quasi nullo. Dopo i costi in ore notturne, con slippage maggiore dei costi diurni [manca], difficilmente passa.
- **Altri vincoli non verificati.** Il WR e lo stop sono ignoti [manca]. Un drift long-only a 1 trade al giorno ha di norma WR vicino al 50% [stima, nessun dato]. Sarebbe sotto il 55%.
- **Per questo non è candidata.** Sono più di uno i vincoli sconosciuti: frequenza di 1 trade al giorno, WR e costi notturni. Come seconda gamba la frequenza di 1 al giorno sarebbe accettabile secondo `come_scegliere_un_paper.md`. Il resto non lo so.
- **Cosa misurare per primo (falsificatore).** Si misura sui dati propri di MES/ES 5 minuti, 2020-2024: il rendimento medio per notte, in punti, di ciascuna fascia di mezz'ora della sessione Globex europea. Serve un valore ≥ 2,6 punti MES netti di un costo notturno realistico. Se nessuna finestra ci arriva, è morta in un'ora. Prima va letto Boyarchenko-Larsen-Whelan per fuso, finestra e se il paper riporta i costi.
- **Da verificare in LucidFlex.** Se la regola «flat a fine giornata» ammette una posizione tra le 23:30 e le 03:30 ET, cioè dentro la stessa sessione CME.

## Quello che le altre fonti dicono: un risultato negativo coerente

- [dev.to, 4 strategie su MNQ](https://dev.to/vikihermes/i-backtested-4-mnq-day-trading-strategies-walk-forward-heres-what-actually-survived-and-the-2h12). La fonte riporta walk-forward su 2 anni di barre a 1 ora (livello 2, campione corto). Fade del gap: PF 1,14 su 163 trade, DD $3.116. Pullback su EMA: PF 0,73. Donchian: PF 1,03. Trend ATR: PF 0,49. Nessuna passa.
- [arXiv 2605.04004 (Mesfin)](https://arxiv.org/pdf/2605.04004). Il classificatore VVG scatta nel 4,4% dei giorni. L'ingresso in reversal ha 35 trade fuori campione e t-net +1,26. L'autore scrive che nessuna regola direzionale fissa sopravvive in tutti e tre gli anni di test.
- [Reading, intraday time-series momentum](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf). Nel paper la prima mezz'ora predice l'ultima in 12 mercati su 16. È la famiglia di LastHalfHour, già in pipeline: non è nuova.
- [Della Corte-Kosowski, Market closure and short-term reversal](https://www.cicfconf.org/sites/default/files/paper_357.pdf). È la famiglia di ON_Reversal. Nei nostri dati è già morta, con t −2,24 su 1.661 trade.

## Osservazioni separate (non toccano i criteri)

1. **Dai dati misurati, le due strategie "in coda" non lo sono più.**
   - `pipeline_semplice.md` dice che VaultBreak `MaxTrades1` «non ha mai visto un OOS». La tabella REPORT MISURATI ha invece `VB_S5_OOS_MaxTrades1_2025-2026`: n 138, **t 0,23**. Fallisce la soglia di 1,3.
   - ORB `cutoff11` ha OOS con t 0,63. Fallisce anche lei.
   - DriftPullback ha OOS con **t 1,86** su 1.439 trade, quindi passa 1,3. `pipeline_semplice.md` la dà come OOS da girare. Il documento è indietro rispetto ai report.
2. **Il t negativo di ON_Reversal (−2,24) e di BTC_First30 variante D (−3,82) non è un'idea.** Specchiare il segno dopo aver visto il risultato è il tipo di scelta fatta a posteriori che il processo vieta. Il bracket specchiato avrebbe pure R:R 1,5 (target 0,75, stop 0,5): fuori dal profilo.
3. **Possibile errore di fuso in `ricerca_18-10.md`.** Il documento colloca l'evento macro alle «8:30 CT», ma i rilasci macro USA escono alle 8:30 ET, cioè le 7:30 CT [stima da conoscenza generale]. Prima di sviluppare quella pista va verificato. Resta fuori dall'ora di DriftPullback in ogni caso, ma è a 2-3 volte a settimana, non 2 al giorno.
4. **Il pattern è sistematico: la frequenza e i costi fanno il lavoro.**
   - Gli effetti con un meccanismo forzato che ho trovato sono **a evento** (FOMC, fix mensili, macro) o **a 1 al giorno** (fix FX, overnight, ultima mezz'ora).
   - Per fare 2 trade al giorno servirebbe un segnale a più alta frequenza. Le fonti lette dicono che questi segnali non reggono dopo i costi, per esempio Krohn ed i due arXiv.
   - Se il mercato fosse questo, il problema è il conto da 50k (rischio per micro e MLL) più che le strategie. Non riscrivo i gate.
5. **Dove spendere le prossime ore.** Probabilmente su DriftPullback e sulla seconda gamba già aperta (LastHalfHour). Va misurata la correlazione sui giorni in cui DriftPullback perde. La pista overnight è da leggere prima di spendere un run.

## Scartate da me

| Idea | Fonte | Motivo |
|---|---|---|
| Fix FX come strategia | [Krohn et al.](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf) | ~$3,4 lordi per micro per trade [stima], 1 fix al giorno: sotto $10 al giorno; gli autori dicono che i costi mangiano i profitti |
| 4pm fix a fine mese | [forexdetox](https://forexdetox.substack.com/p/the-4-pm-london-fix-anomaly-at-month-end) | solo titolo visto: evento mensile, ~12 l'anno [stima] |
| FOMC reversal | [Baglioni-Ribeiro](https://www.researchgate.net/publication/362775066_The_FOMC_Announcement_Reversal) | ~8 trade l'anno; eccesso di reazione, non flusso forzato |
| Reversal macro multi-day | [FEDS 2025-022](https://www.federalreserve.gov/econres/feds/files/2025022pap.pdf) | orizzonte di giorni: viola il flat EOD |
| MOC imbalance | [sellside](https://sellside.substack.com/p/ndr-exclusive-research-moc-imbalance), [Nasdaq](https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27) | richiede i dati NOII a 15:45/15:49 che non abbiamo; sullo SPY 2023 WR sotto il 50% e rendimento cumulato negativo senza soglia |
| Stop-loss cascade e round number | [Osler, NY Fed](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf) | FX spot, non futures (filtro 1); giudicato dal solo titolo e snippet |
| ES/NQ stat-arb intraday | [GitHub index-futures-stat-arb](https://github.com/CommunityPokeOrg/index-futures-stat-arb) | impalcatura senza risultati; solo barre giornaliere |
| MNQ mean reversion «liquidity void» | [GitHub VeteranSand9672](https://github.com/VeteranSand9672/MNQ-Mean-Reversion-Strategy-Research-) | WR 42,86%, regole proprietarie, l'autore stesso dice «preliminare» |
| 4 strategie classiche su MNQ | [dev.to](https://dev.to/vikihermes/i-backtested-4-mnq-day-trading-strategies-walk-forward-heres-what-actually-survived-and-the-2h12) | nessuna passa; campione di 2 anni (livello 2) |
| TORB su indici | [ResearchGate](https://www.researchgate.net/publication/331076454_Assessing_the_Profitability_of_Timely_Opening_Range_Breakout_on_Index_Futures_Markets) | breakout direzionale, rendimenti annui in %, nessun rischio per contratto |
| ORB «+400%» | [Trade That Swing](https://tradethatswing.com/opening-range-breakout-strategy-up-400-this-year/) | affermato, vendor; ORB direzionale |
| Intraday reversal in Cina | [ResearchGate](https://www.researchgate.net/publication/357976845_What_Drives_Intraday_Reversal_Illiquidity_or_Liquidity_Oversupply) | futures cinesi, meccanismo attribuito a retail; testo non disponibile |
| Time-series momentum globale | [Reading](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf) | già LastHalfHour |
| Reversal overnight-intraday | [Della Corte-Kosowski](https://www.cicfconf.org/sites/default/files/paper_357.pdf) | già ON_Reversal (IS t −2,24) |

## Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Ci torno? |
|---|---|---|
| opening range false breakout fade index futures | solo breakout direzionale e vendor | no |
| intraday return predictability + macro reversal | opzioni, cripto, Cina, order flow | no |
| fix FX, pre-fix drift | Krohn et al.: effetto vero, costi lo uccidono | no |
| macro announcement overreaction E-mini | FOMC reversal (8 l'anno), FEDS (multi-day) | no |
| M2K mean reversion strategy backtest | un repo MNQ, due pagine di QuantifiedStrategies | lette solo i titoli: forse |
| NR7 / Crabel | blog e vendor, nessun test su futures con costi | no |
| lead-lag bond/equity | niente di intraday e tradabile | no |
| intraday time-series momentum | LastHalfHour, già coperta | no |
| lunch / midday mean reversion | blog senza test (solo titoli) | no |
| round number / stop orders | Osler (FX spot) | no |
| micro Dow YM intraday | TradingView e GitHub senza dati | no |
| ES/NQ spread | scaffolding senza risultati | no |
| high-volume reversal | Cina, cripto, FX | no |
| European close effect | **ha portato alla pista overnight** | **sì** |
| Boyarchenko-Larsen-Whelan | ultima ricerca bloccata dal limite di chiamate | **sì, la prima da fare** |
| M2K e MYM: specifiche e commissioni | non lette (limite di chiamate) | **sì**, servono tick e commissioni M2K |
| MOC imbalance (3 fonti) | Nasdaq e sellside lette; nexusfi non si apre | no |

```json
{
  "candidates": [],
  "sources_reviewed": [
    {"url": "https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf", "title": "Foreign Exchange Fixings and Returns Around the Clock (Krohn et al., JF 2024; WP Bank of Canada)", "kind": "paper", "verdict": "scartato", "reason": "Effetto vero (~2,5 bp, t 4,5-11,7) con flusso forzato, ma ~$3,4 lordi per micro per trade [stima] e gli autori dicono che i costi mangiano i profitti", "candidate": null},
    {"url": "https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306", "title": "Foreign Exchange Fixings and Returns around the Clock (Journal of Finance 2024, pagina editore)", "kind": "paper", "verdict": "scartato", "reason": "Stesso paper di Krohn et al.; vista solo la scheda", "candidate": null},
    {"url": "https://forexdetox.substack.com/p/the-4-pm-london-fix-anomaly-at-month-end", "title": "The 4 PM London Fix Anomaly at Month-End", "kind": "site", "verdict": "scartato", "reason": "Solo titolo visto: evento mensile, ~12 l'anno [stima]; non aperta", "candidate": null},
    {"url": "https://www.researchgate.net/publication/362775066_The_FOMC_Announcement_Reversal", "title": "The FOMC Announcement Reversal (Baglioni-Ribeiro, 2025)", "kind": "paper", "verdict": "scartato", "reason": "~8 trade l'anno e meccanismo di eccesso di reazione, non flusso forzato", "candidate": null},
    {"url": "https://www.federalreserve.gov/econres/feds/files/2025022pap.pdf", "title": "FEDS 2025-022 (reazione ad annunci macro)", "kind": "paper", "verdict": "scartato", "reason": "Reversal su orizzonte di giorni: viola il flat EOD (da estratto)", "candidate": null},
    {"url": "https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27", "title": "How Much Does the MOC Imbalance Matter? (Nasdaq)", "kind": "site", "verdict": "scartato", "reason": "Spiegazione del meccanismo d'asta con NOII ai professionisti: nessuna regola, dati che non abbiamo", "candidate": null},
    {"url": "https://sellside.substack.com/p/ndr-exclusive-research-moc-imbalance", "title": "NDR: Exclusive Research - MOC Imbalance", "kind": "site", "verdict": "scartato", "reason": "Richiede imbalance preliminare a 15:45/15:49 (dati assenti); su SPY 2023 WR sotto il 50% e cumulato negativo senza soglia", "candidate": null},
    {"url": "https://nexusfi.com/showthread.php?t=60003", "title": "MOC imbalance values in trading (nexusfi)", "kind": "forum", "verdict": "aperto", "reason": "Il fetch è tornato vuoto: non letto", "candidate": null},
    {"url": "https://dev.to/vikihermes/i-backtested-4-mnq-day-trading-strategies-walk-forward-heres-what-actually-survived-and-the-2h12", "title": "4 MNQ day-trading strategies, walk-forward", "kind": "site", "verdict": "scartato", "reason": "2 anni di barre a 1 ora; nessuna delle 4 passa (gap fade PF 1,14, DD $3.116)", "candidate": null},
    {"url": "https://github.com/VeteranSand9672/MNQ-Mean-Reversion-Strategy-Research-", "title": "MNQ Mean Reversion Strategy Research (GitHub)", "kind": "other", "verdict": "scartato", "reason": "WR 42,86%, regole proprietarie e risultati dichiarati preliminari dall'autore", "candidate": null},
    {"url": "https://arxiv.org/pdf/2605.04004", "title": "Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ (Mesfin)", "kind": "paper", "verdict": "scartato", "reason": "Conferma lo scarto: VVG attivo nel 4,4% dei giorni, reversal 35 trade con t-net 1,26, nessuna regola fissa regge in 3 anni", "candidate": null},
    {"url": "https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf", "title": "Intraday time series momentum: global evidence and links to market characteristics", "kind": "paper", "verdict": "scartato", "reason": "Prima mezz'ora predice l'ultima in 12 mercati su 16: famiglia LastHalfHour, già in pipeline", "candidate": null},
    {"url": "https://www.cicfconf.org/sites/default/files/paper_357.pdf", "title": "Market Closure and Short-Term Reversal (Della Corte-Kosowski)", "kind": "paper", "verdict": "scartato", "reason": "Famiglia ON_Reversal, già morta nei nostri dati (IS t -2,24)", "candidate": null},
    {"url": "https://www.researchgate.net/publication/331076454_Assessing_the_Profitability_of_Timely_Opening_Range_Breakout_on_Index_Futures_Markets", "title": "Timely Opening Range Breakout on Index Futures Markets", "kind": "paper", "verdict": "scartato", "reason": "Breakout direzionale, rendimenti annui in % senza rischio per contratto (da estratto)", "candidate": null},
    {"url": "https://tradethatswing.com/opening-range-breakout-strategy-up-400-this-year/", "title": "Opening Range Breakout Strategy up 400% This Year", "kind": "vendor", "verdict": "scartato", "reason": "Affermato, ORB direzionale; solo estratto letto", "candidate": null},
    {"url": "https://www.researchgate.net/publication/357976845_What_Drives_Intraday_Reversal_Illiquidity_or_Liquidity_Oversupply", "title": "What Drives Intraday Reversal? Illiquidity or Liquidity Oversupply?", "kind": "paper", "verdict": "scartato", "reason": "Futures cinesi, meccanismo attribuito al retail; testo non disponibile", "candidate": null},
    {"url": "https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf", "title": "Stop-loss orders and price cascades in currency markets (Osler)", "kind": "paper", "verdict": "scartato", "reason": "FX spot, non futures (filtro 1); giudicato dal solo titolo/estratto", "candidate": null},
    {"url": "https://github.com/CommunityPokeOrg/index-futures-stat-arb", "title": "index-futures-stat-arb (ES vs NQ)", "kind": "other", "verdict": "scartato", "reason": "Impalcatura di ricerca senza risultati; solo barre giornaliere", "candidate": null},
    {"url": "https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/", "title": "Sweet dreams: best times for overnight market returns (MSU Broad)", "kind": "site", "verdict": "aperto", "reason": "Comunicato (livello 2): 100% del rendimento medio E-mini in una finestra di 4 ore, 2006-2018; fuso incoerente, paper non letto, edge e costi [manca]", "candidate": null},
    {"url": "https://arxiv.org/pdf/2507.04481", "title": "Does Overnight News Explain Overnight Returns? (§5.4)", "kind": "paper", "verdict": "aperto", "reason": "Rimanda a Boyarchenko-Larsen-Whelan (2023) e all'inventario degli intermediari; è il paper da leggere per la pista overnight", "candidate": null},
    {"url": "https://www.cnbc.com/2026/10/05/stock-market-today-live-updates.html", "title": "S&P 500 first close above 7,800 (CNBC)", "kind": "site", "verdict": "scartato", "reason": "Non è una fonte di strategia: usata solo per il livello dell'indice nell'aritmetica", "candidate": null}
  ]
}
```

---

## Gate 0 — verifica automatica (gate0.py, nessun modello)

Ricalcolato da codice, non dal ricercatore. `?` = numero non fornito.

| Candidata | Esito | Controlli |
|---|---|---|
