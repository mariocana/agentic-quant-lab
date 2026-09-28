# The Institutional Protocol (Matteo Conti) — digest del materiale

Sintesi di tutto il materiale in `mc/education/protocollo/`: 10 lezioni + 3 extra + 5 live
(19 video trascritti in `mc/education/protocollo/transcripts/`), PDF, template di codice,
glossario, Strategy of the Month e Strategy Feedbacks.
Serve come riferimento per la migrazione su MultiCharts e per il protocollo di test
(`mc/docs/protocollo_test_mc.md`).

---

## 1. Il protocollo (9 step — "se manca uno step, non si trada")

| # | Step | Regola operativa |
|---|---|---|
| 1 | Idea | Ipotesi **falsificabile** in una frase. Fonte principale: paper (SSRN). Leggi solo l'abstract, estrai la claim, fai il backtest più semplice possibile. |
| 2 | Dati | 5–10 anni intraday puliti. Sviluppa sul contratto **più liquido** (NQ, non MNQ: MNQ pre‑2019 è sintetico), poi tradi il micro. Continuous contract per il backtest, front month mappato per il live. |
| 3 | Codifica | Regole 100% oggettive. "Se non si può codificare non si può testare; se non si può testare non si trada". |
| 4 | Backtest | Automatico, su tutto il campione, **1 contratto fisso**, costi realistici (NQ: $2.25–4.50/contratto + 1 tick slippage). |
| 5 | Analisi | Net profit, % profitable, **avg trade**, max DD ($, non %), equity curve. Poi Monte Carlo. |
| 6 | Ottimizza | Due passi: range largo/step grandi → range stretto/step piccoli. Mai "capillare". Pochi input. |
| 7 | Overfitting | IS 80–85% / OOS 15–20%, **OOS toccato una volta sola**. Confronto metriche e EV con intervalli di confidenza sovrapposti. |
| 8 | Deploy | Paper 1 settimana, poi live. Automazione totale, VPS. |
| 9 | Monitoraggio | Avg trade live → converge al backtest (dai ~3 mesi). DD live vs percentili MC: 75° → riduci rischio, 95° → **stop**. Nessuna interferenza discrezionale. |

**Regola di stop**: hard stop = DD live oltre il 95° percentile MC. Soft stop = performance
degli ultimi ~5 mesi annualizzata molto sotto la media storica → revisione, non kill.
Riavvio quando 5 mesi positivi, 12 mesi positivi, ultimi 3 mesi sopra il passo storico.

---

## 2. Soglie e metriche

### Backtest (1 contratto)
- **Avg trade minimo** per coprire i costi (dal PDF `avg_trade_win_thresholds`):
  NQ $70 · **MNQ $10** · ES $75 · MES $10 · YM $70 · MYM $10 · GC $140 · MGC $20 ·
  CL $140 · MCL $14 · 6E $125 · DAX $350 · FDXM $70. "Sano" in generale: ~$100.
- Profit factor 1.2–2 sano; < 1.2 debole.
- Win rate: da leggere insieme al R:R. Con TP 2R serve > 50%; con TP 1R ~58% è già buono.
- Max DD in **$ per contratto**: è quello che decide se la strategia è tradabile (Lezione 8:
  LW breakout NQ, DD $60k su 1 contratto = intradabile, MC reshuffle $112k).
- Max Value DD (perdita cumulata di trade consecutivi) → serve per il sizing.

### Monte Carlo (MultiCharts, built‑in)
- **Reshuffle**: ≥ 1000 sim, 100% dei trade. Mediana net profit > 0, < 5–10% di sim
  in perdita, dispersione stretta, DD peggiore accettabile.
- **Bootstrap/resampling** (Colab): ≥ 10 000 sim. EV in $ e in **R**; CI 95%;
  P(EV ≤ 0) < 5% (IS), < 10% OOS accettabile, < 1% ottimo. CI IS e OOS devono sovrapporsi.
  Percentili di DD dopo 10/20/40/100 trade = i "yardstick" per il live.

### Ottimizzazione
- Non prendere il primo risultato: guarda net profit + % profitable + avg trade + DD
  + n. trade insieme; cerca **cluster stabili** di parametri.
- Blocca i parametri ≥ 1 mese. Non ri‑ottimizzare di continuo.
- Ogni regola aggiunta deve avere una ragione logica (LW breakout: filtro volatilità
  perché i breakout falliscono in bassa vol → ok; VIX e Fear&Greed sull'overnight →
  peggioravano l'avg trade → scartati).
- Base case sempre: la versione **senza filtri** è il benchmark. Un filtro vale solo se
  alza l'avg trade (anche solo tagliando trade marginali = meno commissioni).

### Walk‑Forward (Extra 3, nativo in MC)
- IS 252 sessioni / OOS 63, **rolling** (anchored solo se il regime è stabile).
- Fitness: **profit factor** (non net profit).
- Criteri di robustezza fissati **prima** di lanciare: avg OOS net profit > 0; avg OOS PF
  > 1.1; ≥ 60% delle finestre OOS profittevoli; nessuna finestra > 50% del profitto;
  ≥ 30 trade/finestra; **walk‑forward efficiency ≥ 60%** (< 50% = fit sul rumore).
- Se passa: usi i parametri del "forecast" per i prossimi 63 giorni, poi ri‑ottimizzi.
- Utile con pochi dati e su asset regime‑dipendenti; con lo split classico è più facile
  auto‑ingannarsi cambiando le soglie dopo.

### Sizing
- Metodo 1: max perdita per trade tollerata ÷ peggior trade del backtest.
- Metodo 2 (consigliato): **max DD tollerato ÷ DD** (backtest, o meglio 95° perc. MC).
- Se il numero viene < 1 contratto → micro (÷10) o CFD.
- **Volatility targeting** (Extra 1): contratti = rischio $ target ÷ (vol × prezzo × $/punto);
  non elimina il DD di regime (è il premio al rischio), ma rende ogni trade a rischio
  costante e stringe la dispersione MC. Con cap margine e tetto contratti
  (template `Gold Reversal Target Vol Margin`, `Overnight … Volatility Scaled`).
- **Cushion ladder** (DriftPullback, sez. 08 del tutorial): `cushion = max(0, NetProfit +
  CushionAdj)`; `contratti = base + int(cushion / $2000)`, tetto 3, mai sotto 1. Scala col
  denaro che il mercato ti ha **già** pagato, non con la fiducia: finché la strategia non
  si è guadagnata il primo gradino tradi size minima contro il DD dell'eval, e ogni
  contratto in più è finanziato interamente da profitto bancato. Ricalcolata **una volta
  al giorno**, al reset, mai dentro la sessione. Il vol‑sizing è stato testato contro
  questa ladder e non l'ha battuta a parità di esposizione (Sharpe piatto fra i regimi di
  ATR): è rimasta la ladder, più semplice.
- **I guardrail si scelgono prima del backtest, dalle regole del conto — non dopo, dalla
  curva di equity.** La strategia si adatta al conto, mai il contrario. Corollario
  operativo: cap di ingressi/giorno **e** cap di perdite/giorno, così il worst day è noto
  in anticipo (es. 2 stop × 80 pt) invece di essere scoperto nell'equity curve. Recepito
  nel Gate 0 della pipeline.

---

## 3. MultiCharts / PowerLanguage — cose da sapere (trappole viste nei video)

- **Esecuzione a chiusura barra**: `if Time = 0930 then Buy next bar at market` esegue
  all'apertura della barra **dopo** quella stampata 0930 (con barre 30 min → 10:00).
  Le barre sono timbrate a **fine periodo**. Soluzione: anticipare l'orario di un bar o
  usare `this bar on close`.
- **Timezone**: TradeStation/CME = **Chicago (CT)**. RTH = 08:30–15:00 CT. Il codice che
  "pensa" in ET è di un'ora sfasato: nessun errore, solo statistiche sbagliate.
  Verificare sempre il session template (QuoteManager → Session Templates).
- `[IntrabarOrderGeneration = false]` di default: TP/SL a "next bar at market" scivolano
  di una barra (LW breakout: TP 100 pt → fill a ~$2000 ± varianza). Per fill esatti:
  IOG on, oppure ordini `stop`/`limit` re‑emessi ogni barra, oppure `SetStopLoss`/
  `SetProfitTarget` (in $ per posizione — attenzione allo scaling dei contratti).
- **Max bars back** (Strategy Properties) ≥ lookback più lungo (Donchian 96 → errore
  con 50 di default).
- Errori tipici da LLM: variabile `i` già definita (usare `idx`); array `[500](0)`;
  `return`/`exit` spuri; funzioni inesistenti → crearle (`WilliamsLargeTradeIndex`,
  `VWAP_RTH_Custom`); "floating point invalid operation" = divisione per zero.
- **SL/TP a livello posizione vs contratto**: `SetStopLoss(x)` è per posizione; se metti
  7 contratti devi moltiplicare x per 7. In punti (`EntryPrice - 50`) scala da solo.
  Controllo rapido: lista trade con 10 contratti, lo stop deve essere ×10.
- Dati esterni: CSV `Date,Time,Value` (YYYYMMDD, HHMMSS) → QuoteManager → Add symbol
  (ASCII mapping) → Import. Template Colab per qualunque API.
- Live: chart sul **continuous** (@NQ), `Broker Profiles → Symbol Mapping` → front month
  (aggiornare 2 giorni prima della scadenza). Sviluppa su NQ, mappa su MNQ.
- Auto trading: *Async mode*, "get real‑time data from chart", conferma ordini off,
  stop/limit "emulate locally + send market" con prop/Rithmic, dialog iniziale sempre.
- Coerenza tra data provider: stessi 100 giorni su Sim vs TradeStation → stesso n. trade
  e net profit prima di fidarsi dei 5 anni.
- Multi‑data: Data1 esecuzione, Data2 segnale; **congelare** i valori di Data2 sul
  boundary (`Time of data2 <> t2`) per non sbirciare la barra incompleta.
- Prompt template PowerLanguage (PDF) + template di strategie da dare in pasto all'LLM.

---

## 4. Prop firm — "as a business" (Lezione 10 + Live 1–4 + deck)

- Le prop guadagnano dalle fee: ~9% passa, ~2% incassa (Earn2Trade 2025). Trattarle come
  **budget**, non come investimento: p = 56% a tentativo → 81% in 2, 92% in 3, 96% in 4.
  Budget es. $400 (3 tentativi + attivazione). Stessa strategia identica a ogni tentativo.
- **Per passare non serve un edge**: serve **win rate alto (~60%) e R:R basso
  (0.5–1)**. L'eval non vede la coda (99 × $500, 1 × −$1M passa comunque).
  Due strade: trovare un edge (lunga) o **ingegnerizzare il pass** (alto WR, basso RR).
- **Mai una sola strategia**: 2–3 non correlate (trend following + mean reverting +
  eventi macro). Alta frequenza aggregata (> 90% dei giorni attivi) senza forzare la
  frequenza della singola strategia.
- **Correlazione fra tentativi** (Live 4): i tentativi non sono indipendenti se il regime
  è ostile alla strategia; un basket regge meglio (con corr 0.3: 84% in 6 tentativi vs
  77% singola). Benchare le strategie in drawdown pesante; tenere quelle "in run".
- **Evaluation ≠ funded**: eval = max P(pass) → size relativamente alta (es. 13–17 MNQ
  su NQ drift/ORB); funded = max P(payout) → size **piccola** (2–4 MNQ), obiettivo
  sopravvivere e fare il ladder completo dei payout ($13k su Apex 50k).
  Basket di 3 strategie: qualification 78% vs 52% singola; payout atteso $6.8k vs $3.4k.
- Cushion prima di scalare: statisticamente cambia poco il pass rate, ma dà controllo.
- Regole Apex 50k usate: target $3000, DD $2000–2500 EOD trailing, 21 giorni, 6 mini/60
  micro max, min $150/giorno per la consistency, payout 100% primi $25k.
- Nel codice: solo il numero di contratti cambia fra backtest e live; SL/TP scalati.
- Le prop monitorano gli account: strategie identiche su molti account → rischio ban.
  Randomizzare piccoli ritardi / piccole varianti.
- Colab: `Prop Simulation single/multiple strategies` (link nel PDF Lezione 10).
  Importa direttamente l'export MC "List of trades"; simula path intraday; calcola il
  numero massimo di contratti "affidabile" (95° perc. perdita per contratto vs DD).
- VPS (Chicago) per girare 24/7; AlgoVPS/Contabo. Non serve se giri solo un ORB.

---

## 5. Libreria strategie del corso (cosa c'è e cosa ci interessa)

| Strategia | Famiglia | Strumento/TF | Stato nel corso | Per noi |
|---|---|---|---|---|
| **Fabio Valentini ORB** (`6. Fabio Model`) | breakout ORB | NQ 5m + 30m delta | **Validato**: 823 trade 2021–26, WR 58%, avg $183 netto, PF 1.28, DD $25k, P(EV≤0)=0.001 | È il nostro `OrbBreakout_EA`: range 30 min da apertura, close > high, SL = range low, TP 1R, flat 14:00 CT, filtro delta `Upticks−Downticks ≥ 200`. **Prima strategia da portare.** |
| **VaultBreak NQ** (`5.`, `10.`, `11.`) | vol breakout (noise boundary = open + 0.6×ATR daily) + VWAP | NQ 5m RTH | Long only; WR ~70% ultimi 40 gg; shelved come candidato Apex ma usato nel basket delle live | Trend following n. 2 per il basket. Attenzione: DailyATR "seeded" (expanding) vs "rolling 252" sono due strategie diverse. |
| **DriftPullback v2.1** (Agnello) | momentum + pullback | NQ 5m exec / 15m segnale | Validato, live su funded; avg $77, WR 65%, t‑stat OOS 2.2. **Tutorial completo** in `11. Strategy Feedbacks` (18 pp.) | **Portata**: `mc/strategies/DriftPullback/`. L'unica del corso col profilo prop nativo (WR 65%, R:R 0.5, flat EOD, cap perdite/giorno). Vedi sotto. |
| **VWAP Pullback / VWAP ADX** | mean reverting intraday | NQ 1m, 24h session | Avg $80, PF 1.2, WR 58% (ADX: WR 82%, avg $300 OOS secondo Agnello) | Il **mean reverting** che manca al basket. |
| **VWAP Signal from Paper** | long/short vs VWAP, reverse on cross | NQ 1m | Esempio paper→codice | Solo didattico. |
| **LW Breakout (Donchian 96 + LWTI + volume)** | breakout | NQ 5m | Fallisce: avg $20, DD $60k; con filtro vol 288/20 → avg $71 | Caso di studio del processo. Non tradare. |
| **Long Market Open S&P** | bias | ES 30m | Esempio Lezione 6 | No. |
| **Overnight anomaly** (v1/v2/v3, ONRB v4, RRB v2) | bias overnight | NQ 30m RTH + daily; 5m Globex | Base: avg $104; trend filter → $115; VIX/F&G peggiorano; vol‑targeting; filtro "down day" | Interessante ma **overnight** (fuori dal nostro focus intraday e ostile alle prop). |
| **Gold Asian Range Breakout** (Strategy of the Month lug/ago 2026) | breakout range asiatico | XAUUSD/GC 15m | Vincitore 2 mesi: PF 1.64 e 3.28 live; WR 34%, no TP, stop = range | Simile al nostro range‑breakout; **diversifica da NQ**. Candidato. |
| **Gold 3‑candle Reversal** | pattern | GC 4h | "Funziona ma senza ipotesi" | No (ma il modulo di sizing con cap margine è riusabile). |
| **Volatility Break (z‑score)** | trend continuation vol‑normalized | BTC 15m | Fallisce il WFO (56% finestre positive, WFE bassa) | Solo esempio WFO. |
| **PEAD** | event‑driven | azioni daily | Calmar ~0.68, long only | Fuori scope. |
| **OFB Big Trade / Bridge** | order flow L3 | NQ 1m | Delta/whale poco valore standalone, ok come filtro; hold ottimale 15–20 min | **Fuori dalla pipeline.** Vedi §7: nessuna delle nostre 6 strategie lo usa. |
| N‑Bar / N‑Day breakout | scaffolding | intraday | Template | Utile per imparare `Buy next bar at X stop`. |
| Trend Following Regime Check | diagnostica | 1m | "Compra dopo barra verde, vendi dopo rossa": equity su = regime trend | **Da girare su ogni strumento** prima di scegliere la famiglia. |
| NQ Session Tester | diagnostica | 30m Globex | overnight vs intraday vs B&H | Utile per capire dove sta il rendimento. |

Indicatori/funzioni riusabili: ORB Box (disegna il range), Session High/Low lines,
Cumulative Delta (approssimazione CLV: `Vol × ((C−L)−(H−C))/(H−L)`), Volume POC,
`VolumeProfileLevels` (POC/VAH/VAL), `VWAP_RTH_Custom`, LWTI, Donchian.

Concetti utili emersi:
- Il rendimento di NQ 2015–2026 è **tutto overnight**; l'intraday RTH è piatto. L'ORB
  funziona per motivi strutturali (flussi che possono operare solo dopo le 9:30) e per
  il regime trend post‑2019. Regime check e diversificazione, non "l'ORB per sempre".
- Filtri con valore reale: pochi. Sizing > filtri quando il DD è di regime.
- Fixed points vs ATR: Agnello ha provato 3 volte exit ATR e vol‑filter → mai meglio dei
  punti fissi. Ma con NQ da 15k a 30k i punti fissi non sono confrontabili nel tempo:
  valutare esit in $ o in % (Sebastian, Live 2).
- Competizione mensile: 80% ritorno risk‑adjusted (media/dev.st ritorni giornalieri),
  20% giorni profittevoli/giorni totali; min 3 trade; codice PowerLanguage.

### DriftPullback — cosa si porta via dal tutorial (oltre alla strategia)

Il documento in `11. Strategy Feedbacks` è l'unico del corso che spiega una strategia
*intera*: meccanismo, architettura, ogni input col suo stato di evidenza, walkthrough di
tutti i blocchi di codice, e i limiti onesti dell'implementazione. Cose riusabili ovunque:

- **Chi sta dall'altra parte.** «Se non sai chi sta perdendo soldi contro una strategia,
  non hai una strategia: hai un pattern.» Qui la risposta è esplicita — chi insegue tardi
  paga lo spread al momentum, chi vende la prima discesa restituisce il pullback.
- **Architettura a due orologi.** Il TF lento decide *se* e *in che direzione*, il veloce
  decide *quando*. I valori del TF lento vanno **congelati** dentro la barra (flag di
  confine tipo `newBar2`): un'implementazione ingenua li ricalcola a ogni barra veloce, il
  segnale oscilla tre volte per barra lenta e il backtest sbircia una barra non chiusa.
- **Il fuso orario è il modo più silenzioso di rompere una strategia.** Gli orari sono in
  ora del chart: se sono sbagliati non c'è errore, si trada semplicemente un'ora diversa
  da quella validata e ogni confronto diventa privo di senso. Tabella di conversione ET/CT
  **nel documento della strategia**, non nella testa.
- **Slippage esplicita solo sugli stop.** Gli stop riempiono in mercati veloci e spesso
  peggio del loro prezzo; i limit riempiono al prezzo o non riempiono. Mettere la penalità
  nel backtest, sull'unico tipo di ordine che se la merita (`StopSlipTicks`, convertito con
  `MinMove/PriceScale` così resta portabile), costa meno che scoprirla live. «Il pessimismo
  che scegli batte l'ottimismo che scopri.»
- **Un bracket asimmetrico non è un errore se il meccanismo lo giustifica.** Stop largo e
  target piccolo (R:R 0.5) è coerente con «i pullback dentro un drift si risolvono poco
  profondi e in fretta»: si compra un WR alto su un tragitto corto. È anche esattamente il
  profilo che vogliono le prop.
- **Mappa dell'evidenza.** Non tutti gli switch di una strategia hanno lo stesso supporto:
  il tutorial distingue *validato* (SMA + punti fissi; VWAP di sessione + punti fissi),
  *seed* (i moltiplicatori ATR: valori di partenza per esperimenti tuoi, mai per il live) e
  *logica di deployment* (la cushion ladder: non è edge). Da imitare in ogni nostra SPEC.
- **Limiti dichiarati invece che nascosti**: ingresso valutato alla chiusura della barra di
  pullback e fill all'apertura della successiva; **barra d'ingresso scoperta** (i bracket
  sono ordini next‑bar emessi dalla posizione); contatori esatti solo perché tutte le
  uscite sono next‑bar — se si passa a `SetStopLoss` & co. l'assunzione salta.
- **Non copiarla.** L'autore lo scrive: è uno scheletro da smontare (cambia l'ancora, il
  trigger, lo strumento), non un prodotto finito.

---

## 6. Cosa cambia per noi

1. Il nostro `OrbBreakout_EA` è di fatto il Fabio Model **già validato** (stessa logica,
   R:R 1, long only). Prima porting su PowerLanguage, aggiungendo il filtro delta
   (in MC `Upticks/Downticks` sono nativi; su MT5 non lo erano).
2. Il processo Fase 2 diventa: backtest 1 contratto NQ → MC reshuffle (built‑in) →
   split IS/OOS una volta → Colab bootstrap (EV, CI, percentili DD) → WFO dove ha senso
   → prop simulator → size. Vedi `protocollo_test_mc.md`.
3. Il basket obiettivo per la prop: ORB e VaultBreak (trend NQ) + Gold Asian (altro
   asset) + un lato short reale (NQ First5 o DriftPullback). Stato aggiornato in
   `pipeline_prop.md` / `pipeline_status.json`, non qui.
4. `PropGuard` va riscritto in PowerLanguage; le regole Apex sono note (sopra).
5. Il journal discrezionale non cambia.

---

## 7. Dipendenze — cosa serve davvero per far girare le nostre strategie

| Componente | A cosa serve | Ci serve? |
|---|---|---|
| **MultiCharts** (licenza) | piattaforma, backtest, ottimizzatore, Monte Carlo built‑in, WFO | **Sì.** Il piano free è solo simulazione: non collega feed esterni. |
| **Feed storico** (TradeStation, o dxFeed via MC) | barre 1/5/15 min su @NQ e @GC per IS 2020‑24 + OOS | **Sì.** È il blocco attuale. |
| **Colab** (bootstrap, prop single, prop multiple) | Stage 6, 7, 8 — gratis, si carica il file trade esportato da MC | Sì, già linkati in `pipeline_prop.md`. |
| **The Bridge / OrderFlowBridge** (`9. The Bridge`) | installer Windows che aggiunge a MC una DLL, **16 funzioni PowerLanguage** e un downloader proprio per dati **order flow L3/MBO**; si verifica con `ofb diagnose` | **No.** Vedi sotto. |

### The Bridge: cosa è e perché non ci riguarda (per ora)

È un prodotto a parte (v2.0.9, exe Windows + licenza propria): serve a portare in
PowerLanguage il **flusso ordini a livello 3** — big trade, whale, delta cumulato vero —
che MultiCharts da solo non espone. Ha un suo scaricatore dati e le sue funzioni da
ricompilare nell'editor.

**Nessuna delle nostre 6 strategie lo usa.** Girano tutte su OHLC + volume e su funzioni
native PowerLanguage (`Average`, `AvgTrueRange`, `Volume`/`Ticks`, `MinMove`/`PriceScale`,
`NetProfit`, `PositionProfit`, `TotalTrades`, …). Quello che serve sono **i dati**, e i
dati arrivano da TradeStation o da dxFeed dentro MultiCharts.

L'unico punto di contatto è il **filtro delta opzionale dell'ORB**
(`UpTicks − DownTicks ≥ 200`, `UseDeltaFilter` **0 = spento di default**): `UpTicks` e
`DownTicks` sono parole riservate **native** di MultiCharts, alimentate dai dati tick del
feed — non dal Bridge. Se un giorno servisse, basta storico tick, non l'installer.

Dal corso, inoltre, il verdetto sull'order flow è tiepido: delta e whale hanno **poco
valore standalone**, vanno al più come filtro. Un filtro va comunque validato con lo
split‑sample come ogni altro — e prima di allora servono sei strategie che passino i gate
senza. Il Bridge resta materiale di studio in `mc/education/protocollo/OrderFlowBridge/`.
