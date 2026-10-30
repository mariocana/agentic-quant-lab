<!-- researcher.py, 20/10/2026, model claude-opus-5-5, effort high -->

# Ricerca candidate LucidFlex 50k: sessione del 20/10/2026

## 0. Esito

1. **Non ho trovato candidate nuove che superino i filtri eliminatori 1, 3 e 5** (testata su futures, flusso forzato, chiusura entro la giornata) con almeno un segnale al giorno. Fra i paper trovati, l'unico filone che li supera è il momentum di fine giornata da hedging (Gao-Han-Li-Zhou e Baltussen et al.). Dovrebbe essere la cartella `LastHalfHour`, quindi non lo ripropongo. Questo conferma quanto dice `come_scegliere_un_paper.md`: lo spazio utile è stretto.
2. Il risultato più utile riguarda la lista "cosa resta da provare" del 18/10. **Una voce va tolta** (Xu-Zhu). **Una seconda va bloccata finché non si chiarisce un punto in archivio** (DriftPullback su YM): secondo i miei conti probabilmente non passa lo screening dei $10 al giorno per micro. **La terza ha un orario da verificare** (evento macro).
3. **Avvertenza:** il limite di ricerche si è esaurito dopo circa 14 query. Nella tabella 7.2 alcuni filoni risultano aperti perché ho finito il budget, non perché fossero vuoti.

**Specifiche dei contratti.** Le ho prese da pagine di broker, perché non sono riuscito a raggiungere il sito CME. Vanno ricontrollate su CME, come chiede il prompt.
- MYM: $0,50 × indice DJIA, tick 1,00 = $0,50 [fonte: [AMP](https://www.ampfutures.com/trading-info/contract-specifications)]
- MNQ: $2 × indice, tick 0,25 = $0,50 [fonte: AMP]
- M2K: $5 × indice, tick 0,10 = $0,50 [fonte: AMP]
- MES: moltiplicatore $5, tick $1,25 [fonte: [NinjaTrader](https://ninjatrader.com/futures/futures-contracts/micro-vs-mini-futures-comparison/)]

---

## 1. Tabella di sintesi

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato (punti → $/micro) | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| 1 | DriftPullback su YM | MYM · TF come la SPEC [manca] | momentum + overlay di pullback | 129 pt [fonte: ricerca_18-10] → **$64,50** [stima: 129 × 0,50] | [manca] (su NQ circa 700 [stima: 3.499/5]) | [manca] (NQ 63,5%) | [manca] (NQ 0,64) | interna + [Fast Alpha](https://concretumgroup.com/wp-content/uploads/2026/02/Improving-Performance-with-Fast-Alphas-A-Tactical-Overlay-for-Intraday-Trend-Trading.pdf) | **QUASI**: sfora lo screening dei $/giorno per micro [stima]. Va prima verificato che il run non sia già stato fatto |
| — | Momentum ultima mezz'ora (Gao / Baltussen) | — | momentum | — | — | — | — | [Baltussen et al.](https://academicweb.nd.edu/~zda/intramom.pdf) | **non riproposta**: è `LastHalfHour`, già in cartella |
| — | Evento macro | MES/MYM | evento | [manca] | circa 100-150 [stima: 2-3 a settimana × 50] | [manca] | [manca] | board interno | **non candidata**: frequenza 0,4-0,6 al giorno e nessuna regola testata in letteratura (vedi §3) |
| — | Reversal pomeridiano (Xu-Zhu) | — | mean reversion | — | — | — | — | [SSRN 4192163](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4192163) | **scartata**: cross-section azionario, falliscono i filtri 1 e 5 |

---

## 2. Scheda della quasi-candidata

### #1 DriftPullback su MYM: QUASI-CANDIDATA

**Non è un risultato della mia ricerca.** È la prima voce del board del 18/10 ("un run"). La metto qui perché ho un conto che conviene fare prima di spendere quel run.

**⚠ Da verificare prima di tutto.** `come_scegliere_un_paper.md` scrive che *Fast Alpha* "era su SPY, e su YM non si è trasferito". Fast Alpha è la fonte di DriftPullback. Se la frase si riferisce a un run DriftPullback su YM già fatto, la candidata è già morta. Va controllato in archivio prima di qualunque altra cosa.

- **IPOTESI.** Il segnale di drift con ingresso su pullback, che su @NQ ha t 3,01 su 3.499 trade [fonte: prop_vs_live.md], esiste anche su @YM con lo stop riscalato.
- **PERCHÉ DOVREBBE FUNZIONARE.** Zarattini e Pagani usano un segnale di reversal a orizzonte molto corto come overlay di esecuzione su un modello di trend intraday. Lo descrivono come un modo per migliorare il timing d'ingresso [fonte: [Fast Alpha, feb. 2026](https://concretumgroup.com/wp-content/uploads/2026/02/Improving-Performance-with-Fast-Alphas-A-Tactical-Overlay-for-Intraday-Trend-Trading.pdf)]. **Chi perde i soldi: non lo so dire con precisione.** Il reversal di brevissimo periodo è il classico compenso per chi fornisce liquidità. Ma la fonte non identifica un flusso forzato dietro il drift. È un segnale debole, ed è il motivo per cui la scheda sotto ha il punto 3 vuoto.
- **REGOLE.** Sono quelle di `mc/strategies/DriftPullback/SPEC.md`, che non ho; non le riscrivo a memoria [manca]. I cambi sono tre:
  1. simbolo @YM;
  2. drift espresso in ATR e non in percentuale, che è la condizione per sbloccarlo;
  3. stop fisso a 129 pt. Se nel codice lo stop è in ATR, servono un tetto e un pavimento in punti (anti-pattern 2).
- **RISCHIO PER TRADE.** 129 pt × $0,50 = **$64,50 per micro** [stima]. Con 2 tick di slippage sullo stop si arriva a 131 pt, cioè $65,50 [stima]. È 0,13 volte il tetto di $500. Rapporto stop/ATR: 129/420 = 0,31 [stima; l'ATR di 420 è quello stimato nel prompt e va misurato].
- **PERCHÉ RISPETTA IL PROFILO.** Su NQ lo rispetta: WR 63,5% con R:R 0,64 [fonte]. La forma la impone il bracket (ricerca_18-10), quindi su YM la geometria si può replicare. **L'eccesso sul caso invece no: va misurato.**
- **IL VINCOLO SFORATO: $ al giorno per micro** [stima]. Su NQ il dato è $18,34 [fonte: prompt].
  - Un ATR di YM vale 420 × 0,50 = $210 per micro; uno di NQ vale 260 × 2 = $520. Il rapporto è **k = 0,40** [stima, da ATR non misurati].
  - **Ipotesi A**, tutto scala con k: 18,34 × 0,40 ≈ **$7,4 al giorno**.
  - **Ipotesi B**, scala il lordo e i costi per contratto restano fissi:
    - lordo NQ ≈ 5,73 + 1,50 (commissione) + 0,365 × 1,00 (slippage sulle uscite in stop) ≈ $7,60 per micro;
    - lordo YM ≈ 7,60 × 0,40 ≈ $3,07;
    - costi YM ≈ 1,50 + 0,365 ≈ $1,87. Ho supposto la stessa commissione di NQ, ma il costo di YM non è nei documenti [manca];
    - netto ≈ $1,20 per trade, cioè **≈ $3,9 al giorno** a 3,2 trade al giorno.
  - **In entrambi i casi siamo sotto i $10**, fra 0,4 e 0,75 volte la soglia. Normalizzando per nozionale (circa 2,5 MYM per ogni MNQ) si arriva a circa $9,5 al giorno contro $18,34: **lo stesso segnale vale circa metà**. È la tabella "tick per ATR" del prompt (YM a 0,40× di NQ) che si traduce in dollari.
- **COSA LA FALSIFICA.** Sono misure da un'ora, da fare prima del backtest:
  - (0) La frase in archivio: se il run YM esiste ed è negativo, la candidata è morta.
  - (1) Misurare l'ATR14 di YM e NQ per anno sul 2020-2024 e ricalcolare k. Se 18,34 × k è sotto 10, la candidata è morta con lo screening attuale; vedi però l'osservazione 4.1.
  - (2) L'eccesso sul caso su YM con stop a 129 pt, misurato con l'indicatore di misura. **Soglia proposta da pre-registrare:** sotto +1,4 pp (metà del +2,8 di NQ) si uccide.
  - (3) La correlazione del P&L giornaliero con DriftPullback su NQ. Sopra 0,8 è un sostituto, non un'aggiunta al basket. I documenti danno una correlazione intraday fra indici di 0,8-0,95.
- **FONTE.** Fast Alpha: testato dagli autori, ma su SPY. Il nostro test su @NQ futures è "testato con dati e costi".
- **COSA NON SO.** Frequenza, WR, R:R ed eccesso su YM; costo andata-ritorno di YM nel nostro modello; ATR misurati.

**Scheda del filtro sui paper**

| # | domanda | risposta |
|---|---|---|
| 1 | testato su futures | sì, ma **da noi** su @NQ; il paper è su SPY |
| 2 | replicato | no |
| 3 | flusso forzato | **non documentato** [manca]. Il team lo ha già accettato in casa sulla base del t interno |
| 4 | costi | sì nel nostro test ($7,50 per lato + 2 tick sullo stop) |
| 5 | intraday e flat | sì, 3,2 trade al giorno su NQ |
| 6 | anni dalla pubblicazione | circa 0,7 [stima: febbraio → ottobre 2026] |
| 7 | t del paper ≥ 3 | [manca]; il nostro t IS è 3,01 |

---

## 3. Note sul resto del board del 18/10

**Reversal pomeridiano (Xu-Zhu): da togliere, risparmia mezza giornata.** Dall'abstract si vede che è un'anomalia del **cross-section azionario**: "Afternoon returns negatively predict future returns, while morning returns positively predict future returns" ([SSRN 4192163](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4192163)). Il paper precedente di Xu costruisce strategie cross-sectional su titoli e le confronta con i fattori di rischio ([SSRN 2991183](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2991183)).
- Il filtro 1 cade: azioni singole.
- Il filtro 5 cade quasi certamente: i "rendimenti futuri" sono successivi alla giornata. Ho letto solo l'abstract, quindi va confermato sul testo.

**Evento macro: c'è un orario da verificare.** Il board scrive "8:30 CT". I dati USA principali, come PIL e CPI, escono alle **8:30 ET**, un'ora prima dell'apertura azionaria ([Gao et al.](https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf)). In CT sono le **7:30**; le 8:30 CT sono l'apertura del cash. Se la piattaforma è in CT, "ora libera" va ricontrollata. Sulla letteratura:
- Il drift **prima** degli annunci di NFP, ISM e PIL esiste: 10,1, 9,1 e 7,5 bp [fonte: [Hu-Pan-Wang-Zhu, SAIF](https://en.saif.sjtu.edu.cn/junpan/PreAnn_20210302.pdf)]. Però è un rendimento **overnight** ([ABFER](https://abfer.org/component/edocman/main-annual-conference/premium-for-heightened-uncertainty-explaining-pre-announcement-market-returns)), quindi incompatibile col flat EOD, ed è un premio per il rischio, non un flusso forzato.
- Il drift dei 30 minuti prima del rilascio segue la direzione della **sorpresa**: E-mini 2008-2014, 7 annunci su 21 [fonte: [Kurov et al., ECB WP 1901](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1901.en.pdf)]. Gli autori lo attribuiscono a trading informato, cioè l'opposto di un flusso forzato.
- **Una regola di prezzo testata sul dopo-rilascio non l'ho trovata.** Resta un'idea da misurare, non una candidata. A 0,4-0,6 segnali al giorno [stima: 2-3 a settimana] è anche sotto il circa 1 al giorno chiesto per una seconda gamba.

---

## 4. Osservazioni separate

Seguo la regola di processo: queste osservazioni non cambiano i criteri.

1. **Lo screening dei $10 al giorno per micro non tiene conto del nozionale.** Un micro di MYM vale circa 0,4 ATR-dollari di un micro di MNQ [stima]. Lo screening uccide meccanicamente qualunque port su MYM o M2K, anche quando il rischio per micro è 2,5 volte più piccolo. Un metro per dollaro di rischio, o per micro NQ-equivalente, sarebbe più neutro. Anche così, DriftPullback su YM resterebbe a circa metà di quella su NQ (§2).
2. **Lo scarto di MGC nella v4 si appoggiava al budget di R di $60-110**, che viene dal Gate 3 ritirato il 15/10. Quel motivo si è indebolito. Non riapro comunque l'oro, perché ho trovato solo pattern pre-2015 (vedi scarti).
3. **I documenti si contraddicono sulla famiglia trend.** Il prompt la esclude per costruzione; ricerca_18-10 dice che la forma la impone il bracket. Di fatto il team accetta segnali di momentum con bracket (DriftPullback, LastHalfHour). Conviene scriverlo esplicitamente nel prompt.
4. **Stato del basket.** `pipeline_semplice` (15/10) dà ORB cutoff11 e VaultBreak MaxTrades1 "in coda". `cosa_uccide` (17/10, più recente) li dà morti all'OOS, con t 0,63 e 0,23. Viva resta solo DriftPullback, quindi due posti liberi su tre.
5. **Nessun testo nelle pagine consultate conteneva istruzioni rivolte a me.**

---

## 5. Candidate scartate (una riga)

- **Xu-Zhu, reversal pomeridiano:** cross-section azionario, orizzonte oltre la giornata.
- **Drift prima di NFP, ISM e PIL:** è overnight, è un premio per il rischio, circa 36 eventi l'anno [stima: 3 × 12].
- **Drift nei 30 minuti prima dei dati:** trading informato, direzione non nota prima, 7 annunci, campione fermo al 2014.
- **Momentum di fine giornata (Barbon et al., ETF a leva + opzioni):** azioni singole e gamma delle opzioni; la versione su futures è LastHalfHour.
- **Prodotti VIX a leva:** future VX, che a memoria sono Cboe e non CME (da verificare), e l'effetto si inverte overnight.
- **Fix dell'oro del pomeriggio a Londra:** pattern del 2004-2013, prima della riforma con asta IBA, attribuito a possibile manipolazione e non a un flusso.
- **Noise Area:** lo scarto è confermato da una replica fuori campione che trova un degrado.

---

## 7.1 Scartate da me

| Idea | Fonte (link) | Motivo dello scarto in una riga |
|---|---|---|
| Reversal pomeridiano / momentum del mattino (Xu-Zhu 2022) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4192163 | Cross-section azionario; previsione oltre la giornata: falliscono i filtri 1 e 5 |
| Reversal, momentum e rendimenti intraday (Xu 2017) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2991183 | Stessa logica, strategie cross-sectional su titoli |
| Rendimenti prima di NFP, ISM e PIL (Hu-Pan-Wang-Zhu, JFE) | https://web.mit.edu/wangj/OldFiles/www/pap/HuPanWangZhu19.pdf | Finestra overnight; premio per l'incertezza, non flusso forzato; circa 36 eventi l'anno |
| Drift prima dei dati macro su E-mini (Kurov-Sancetta-Strasser-Wolfe) | https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1901.en.pdf | Trading informato; direzione della sorpresa non nota prima; 7 annunci; 2008-2014 |
| Trading informato durante il lockup FOMC (Bernile-Hu-Tang, JFE 2016) | https://www.sciencedirect.com/science/article/abs/pii/S0304405X16300812 | 8 eventi l'anno; trading informato |
| Noise Area (Zarattini-Aziz-Barbon), replica fuori campione | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7290621 | Conferma lo scarto: degrado fuori campione documentato da una replica indipendente |
| ETF a leva + delta hedging delle opzioni a fine giornata | https://ssrn.com/abstract=3925725 | Azioni singole; richiede la gamma delle opzioni; versione futures = LastHalfHour |
| Flussi di ribilanciamento dei prodotti VIX a leva | https://www.sciencedirect.com/science/article/abs/pii/S0378426621002363 | Future VX, che a memoria non sono CME; effetto invertito overnight |
| Fix dell'oro del pomeriggio a Londra su COMEX | https://www.lbma.org.uk/alchemist/issue-73/has-there-been-a-decade-of-london-pm-gold-fixing-manipulation | Pattern 2004-2013, prima della riforma; manipolazione e non flusso; MGC |
| Riforma del fix di oro e argento | https://bearworks.missouristate.edu/cgi/viewcontent.cgi?article=1565&context=articles-cob | Studio su manipolazione prima e dopo la riforma, nessuna regola tradabile |
| Momentum intraday in serie storica, Cina (Jin et al., JFM) | https://hull-repository.worktribe.com/OutputFile/3303156 | Futures cinesi; stessa famiglia di LastHalfHour |
| Momentum intraday in serie storica fra mercati diversi | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4651331 | Famiglia LastHalfHour, uscita in chiusura; testo non letto [manca] |
| Squilibri di order flow e notizie macro su E-mini | https://arxiv.org/pdf/2508.06788 | Richiede dati di book (BBO al secondo) |
| Informazione macro incrementale e momentum intraday | https://www.sciencedirect.com/science/article/pii/S1059056026007926 | Azioni singole |
| Futures sull'indice brasiliano e sorprese macro USA | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7403718 | Mercato B3, non CME; event study senza regola |
| Qualunque port "stessa logica, strumento più piccolo" su MYM o M2K | aritmetica, §2 | A parità di eccesso vale circa 0,4-0,75 volte in $ al giorno per micro [stima]: va misurato k prima |

## 7.2 Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| "Xu Zhu intraday afternoon reversal index futures" | I due paper di Xu; letteratura cinese sul momentum intraday | No: filone esaurito per noi |
| "macroeconomic announcement intraday momentum equity index futures" | Event study, momentum di fine giornata più forte nei giorni di notizie | Poco |
| "intraday return periodicity futures (Heston-Korajczyk-Sadka)" | Solo il paper originale su azioni | **Sì**: periodicità per mezz'ora sui futures non trovata, filone aperto |
| "leveraged ETF rebalancing end of day momentum futures" | Barbon et al.; prodotti VIX | No: coperto da LastHalfHour |
| "Zarattini intraday momentum futures" | Replica fuori campione di Paz (degrado) | No |
| Specifiche micro CME | Pagine di broker (AMP, NinjaTrader) | **Sì**: rifare su cmegroup.com |
| "post-announcement drift E-mini 8:30" / "macro release reversal S&P futures" | Kurov et al.; Hu-Pan-Wang-Zhu | Sì, ma solo per una regola di prezzo dopo il rilascio nell'orario regolare (dati delle 10:00 ET), non trovata |
| "intraday time-series momentum Journal of Futures Markets 2024" | Cina, momentum fra mercati | Poco |
| "execution algorithms top of the hour price pressure" | Niente di pertinente | Forse, con altre parole chiave |
| "Fast Alpha Zarattini Pagani" | Paper Concretum, febbraio 2026 | Sì, per leggere i dettagli dell'overlay |
| "crude oil settlement window / TAS" | Solo FAQ e un'affermazione da forum sul settlement | **Sì**: pressione nella finestra di settlement degli index futures, **non coperto** |
| "Hu Pan Wang Zhu pre-announcement" | Conferma che la finestra è overnight | No |
| "gold futures London PM fix" | Pattern prima del 2015 | Forse: l'asta IBA dopo il 2015 sui COMEX non è coperta |
| **Non fatte per esaurimento del budget** | Fix FX delle 16:00 di Londra su micro FX CME; effetti incondizionati dello 0DTE; Quantpedia; ricerca sistematica sul Journal of Futures Markets | **Sì, tutte aperte** |

```json
[
  {
    "name": "DriftPullback su YM (port interno)",
    "instrument": "MYM",
    "timeframe": "come SPEC DriftPullback (non disponibile)",
    "family": "trend",
    "status": "quasi",
    "quasi_violation": "Screening $/giorno per micro stimato $3,9-7,4 contro soglia $10 (0,4-0,75x), da ATR non misurati (k = 210/520 = 0,40). Prima verificare se il run su YM esiste gia': come_scegliere_un_paper.md dice che Fast Alpha 'su YM non si e' trasferito'",
    "stop_points": 129,
    "risk_usd_micro_claimed": 64.5,
    "trades_per_year": null,
    "win_rate_expected": null,
    "rr_expected": null,
    "flat_eod": true,
    "paper_filter": {
      "tested_on_futures": true,
      "replicated": false,
      "forced_flow": null,
      "costs_reported": true,
      "intraday_flat": true,
      "years_since_publication": 0.7,
      "paper_t_ge_3": null
    },
    "falsifier": "(0) Run YM gia' presente in archivio con esito negativo = morta. (1) ATR14 per anno 2020-2024 di YM e NQ: se 18,34 x k < 10, fallisce lo screening. (2) Eccesso sul caso su YM con stop 129 pt sotto +1,4 pp = kill. (3) Correlazione del P&L giornaliero con DriftPullback NQ > 0,8 = sostituto, non aggiunta al basket",
    "sources": [
      "mc/docs/ricerca_18-10.md",
      "mc/docs/prop_vs_live.md",
      "mc/docs/come_scegliere_un_paper.md",
      "https://concretumgroup.com/wp-content/uploads/2026/02/Improving-Performance-with-Fast-Alphas-A-Tactical-Overlay-for-Intraday-Trend-Trading.pdf",
      "https://www.ampfutures.com/trading-info/contract-specifications"
    ]
  }
]
```

---

## Gate 0 — verifica automatica (gate0.py, nessun modello)

Ricalcolato da codice, non dal ricercatore. `?` = numero non fornito.

| Candidata | Esito | Controlli |
|---|---|---|
| DriftPullback su YM (port interno) | **FAIL** | OK risk per micro <= $500: 129 pt x $0.5/pt MYM = $64 (0.13x the cap)<br>OK researcher's arithmetic: declared $64, recomputed $64<br>? trades/year >= 40: missing<br>OK flat at end of day: True<br>OK 1. tested on futures: True<br>NO 3. forced-flow mechanism: not shown<br>OK 5. intraday, flat within the session: True |
