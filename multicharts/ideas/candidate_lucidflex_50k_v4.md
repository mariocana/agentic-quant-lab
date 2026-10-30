# Candidate per LucidFlex 50k: ricerca del 14/10/2026

Il documento non contiene backtest. Per ogni numero indico la natura: **[fonte]** se l'ho preso da una fonte, **[stima]** se l'ho ricavato io con un'aritmetica dichiarata, **[manca]** se non ce l'ho.
Non ho potuto misurare gli ATR per anno, perché il download dei dati storici (stooq) è stato bloccato da una verifica JavaScript. Tutti gli ATR che uso sono quelli **stimati** del tuo prompt. Vanno misurati prima di tutto il resto.

---

## 0. In sintesi

1. **Nessuna fonte che ho letto mostra, a livello di singolo trade e al netto dei costi, un PF ≥ 1,3 con WR ≥ 55% su un futures su indice intraday.** Le evidenze migliori che ho trovato indicano un vantaggio sul caso di **+1,5…+5 punti percentuali** di win rate. Il tuo profilo ne richiede **+6…+8** (sezione 2). È il risultato più importante della ricerca e va letto prima delle candidate.
2. Propongo **4 candidate**. Due hanno qualche dato descrittivo a supporto (IB-C Breakout e IB-C Failure su MYM/M2K), due sono deboli (Gap fade piccolo, VWAP fade di metà giornata). **Nessuna quasi-candidata:** tutto quello che sforava sforava almeno due vincoli ed è finito negli scarti.
3. **Strumento:** misurato al budget di rischio in dollari che il drawdown consente, **MYM e M2K battono MNQ su entrambi i fronti** e MES è il più caro. Il trade-off "MNQ fine ma rischioso, altri grossolani ma sicuri" vale se lo misuri in tick. Misurato in R non vale più (sezione 1.1).
4. Sul conto ho trovato **tre fatti nuovi** che non erano nel prompt. Li segnalo nella sezione 6 senza toccare i gate: la regola di inattività è più blanda di come la descrivi, i payout richiedono 5 giorni da almeno $150 e la commissione sui micro non scala di 1/10.

---

## 1. Due conti che cambiano dove cercare

### 1.1 Costo per unità di R, al budget che il drawdown concede

Il tuo budget di R è **$60–110 per micro**, cioè $600–1.100 sul contratto grande. Il costo andata-ritorno espresso in R dipende quindi **solo dal costo in dollari per contratto grande** e non dall'ATR. L'ATR conta per un'altra cosa: quanto è grande R rispetto al rumore.

| Strumento | Costo A/R grande | Costo in R (R = $1.100 grande) | R ammesso in punti | R / ATR (ATR del prompt) | Costo A/R micro [stima] | Costo micro in R ($110) |
|---|---|---|---|---|---|---|
| NQ / MNQ | $15 (tuo) | 1,4% | 30–55 | **0,12–0,21** | $1,00 comm. + $1,00 slippage = $2,00 | 1,8% |
| YM / MYM | ~$13,5 [stima] | **1,2%** | 120–220 | **0,29–0,52** | $1,00 + $1,00 = $2,00 | 1,8% |
| RTY / M2K | ~$13,5 [stima] | **1,2%** | 12–22 | **0,30–0,55** | $1,00 + $1,00 = $2,00 | 1,8% |
| GC / MGC | $25 (tuo) | 2,3% | 6–11 | 0,20–0,37 | $1,60 + $2,00 = $3,60 | 3,3% |
| ES / MES | $30 (tuo) | **2,7%** | 12–22 | 0,20–0,37 | $1,00 + $2,50 = $3,50 | **3,2%** |

- Le commissioni Lucid per lato sono $0,50 sui micro indice, $0,80 su MGC e $1,75 sui mini indice **[fonte: TradersPost, PropTradingVibes, che riportano l'help center Lucid]**. La slippage di 1 tick per lato è **una mia ipotesi**, la stessa formula implicita nei tuoi $15 su NQ e $30 su ES. Per YM/RTY il risultato è $1,75 + $5 di tick = $6,75 per lato, cioè $13,5 andata-ritorno.
- **Conseguenza 1.** Al budget di R in dollari, MYM e M2K sono **più economici di MNQ** in unità di R e danno a R **2,5 volte più spazio** rispetto all'ATR. Su MNQ lo stop ammesso è 0,12–0,21 ATR, che è rumore. Lo considero il motivo strutturale per cui tre strategie su NQ sono morte sullo stesso numero.
- **Conseguenza 2.** **MES è lo strumento peggiore** per costo/R, sia sul grande sia sul micro. Lo uso solo come controllo.
- **Conseguenza 3.** Sviluppare sul contratto grande e poi operare sui micro **sottostima i costi**: su MNQ $2,00 contro $1,50 (×1,33), su MGC $3,60 contro $2,50 (×1,44). Il backtest va rifatto con il costo del micro.
- **Rischio di questa tabella.** M2K è il micro indice meno liquido (si cita uno spread tipico di 1 tick in RTH e 2 tick fuori orario). La slippage reale su M2K e MYM va misurata, perché 1 tick può essere ottimistico.

### 1.2 Il numero che uso come falsificatore unico: eccesso sul caso

Prendi un trade con stop S e target T, con R:R = T/S. Se il prezzo fosse un random walk senza drift, la probabilità di toccare T prima di S sarebbe **S/(S+T) = 1/(1+R:R)** (il "null"). Il PF vale WR·R:R/(1−WR). Da qui:

| R:R | WR null | WR per PF 1,3 | eccesso richiesto | WR per PF 1,4 | eccesso richiesto |
|---|---|---|---|---|---|
| 0,50 | 66,7% | 72,2% | +5,6 pp | 73,7% | +7,0 pp |
| 0,60 | 62,5% | 68,4% | +5,9 pp | 70,0% | +7,5 pp |
| 0,80 | 55,6% | 61,9% | +6,3 pp | 63,6% | +8,1 pp |
| 1,00 | 50,0% | 56,5% | +6,5 pp | 58,3% | +8,3 pp |

Gli eccessi sono **lordi**: i costi del micro aggiungono circa +1 pp (MYM/M2K) o +2 pp (MES). L'eccesso richiesto resta quasi uguale per ogni R:R, quindi **cambiare il rapporto target/stop non crea edge, lo rietichetta e basta**. Lo dice in modo esplicito anche la fonte più utile che ho trovato (tradingstats.net, sezione 3).

**Le evidenze esistenti, misurate con questo metro:**
- Il tuo ORB su NQ aveva WR 52,7% con R:R 0,955. Il null è 51,2%, quindi l'eccesso era **+1,5 pp** e il PF lordo circa 1,06.
- Fade degli estremi di sessione sui quattro indici: secondo tradingstats.net, per ogni ampiezza di stop il prodotto WR × payoff resta vicino al pareggio prima dei costi. Eccesso **≈ 0**.
- Lo stesso studio, filtrato con il loro grader proprietario (A+/A), dà circa il 70% di target prima dello stop a 0,20 ATR, che gli autori chiamano un piccolo edge positivo. Con un R:R tra 0,4 e 0,75 (non dichiarato) l'eccesso va da **0 a +5 pp** [stima].
- Breakout dell'IB su ES/NQ, 2015–2025: il rapporto tra MFE mediana e MAE mediana è circa 1,1 [fonte]. È coerente con un eccesso di pochi punti.

**Il test di un'ora per ogni candidata:** dai dati a 1 minuto 2020–2024, ingresso alle regole dichiarate, risoluzione a primo tocco (se una barra tocca entrambi, conta come stop). L'eccesso netto sul null deve essere **≥ +8 pp in aggregato e positivo in ogni anno**. Se non lo è, la candidata muore prima di scrivere il backtest completo.

### 1.3 Quanto ci vuole a passare (Monte Carlo i.i.d., 20.000 simulazioni)

Ipotesi: edge reale, un trade al giorno, R = $100/micro, MLL $2.000 trailing EOD che si blocca a +$100, target +$3.000.

| PF | micro | P(passa) | trade mediani per passare |
|---|---|---|---|
| 1,3 | 1 | 0,98 | 222 |
| 1,3 | 2 | 0,83 | 91 |
| 1,4 | 1 | 1,00 | 180 |
| 1,4 | 2 | 0,91 | 78 |
| 1,4 | 3 | 0,79 | 47 |
| 1,4 | 4 | 0,69 | 29 |

Con 40 trade l'anno e 2 micro passare richiede circa **2 anni**. Con 120–150 trade l'anno ne bastano circa 6–8 mesi. **La frequenza conta per la velocità ben prima che per l'inattività.** Fra due candidate equivalenti preferisci quella più frequente. Il modello i.i.d. sovrastima P(passa), per lo stesso motivo per cui sottostima il drawdown.

---

## 2. Tabella di sintesi (dalla migliore alla peggiore)

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato (punti → $/micro) | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **IB-C Breakout a target fisso** | MYM (alt. M2K) · 1 min | breakout, target piccolo fisso | MYM clamp(0,40·ATR; 120; 200) → **$60–100**; M2K clamp(0,40·ATR; 12; 20) → $60–100 | ~60–80 [stima: C chiude fuori dall'IB nel 33,7% dei giorni ES] | **[manca]**; serve ≥ 63,6% (null 55,6%) | 0,80 per costruzione | tradingstats IB (descrittivo, senza costi) | **CANDIDATA**, da falsificare con il test 1.2 |
| 2 | **IB-C Failure → midpoint** | MYM (alt. M2K) · 1 min | mean reversion, falso breakout | estremo di C + 0,05·ATR, clamp 100–200 → **$50–100** (M2K 10–20) | ~45–65 [stima: C fallita nel 30% dei giorni ES, meno gli scarti per R:R] | **[manca]**; serve ~61–64% | 0,5–1,0 (filtro) | tradingstats IB (descrittivo) | **CANDIDATA**; frequenza da sola al limite, da accorpare alla #1 |
| 3 | **Gap piccolo fade → chiusura precedente** | MYM (M2K; MES come controllo) · 1 min | gap fade | clamp(1,3·\|gap\|; 120; 200) → **$60–100** (M2K 12–20) | ~50–90 [stima, distribuzione dei gap da misurare] | **[manca]**; il 77,8% di riempimento su NQ **non è** un WR | 0,5–1,0 (filtro) | tradingstats gap NQ (descrittivo); Grant-Wolf-Yu 2005 (con costi: l'edge si riduce molto); Iwanaga-Sakemoto 2026 (si indebolisce dopo il 2010) | **CANDIDATA DEBOLE** |
| 4 | **VWAP fade di metà giornata (regime 0DTE)** | MYM e MES · 5 min | mean reversion intraday | clamp(1,3·deviazione; 120; 200) su MYM → **$60–100**; MES 12–20 pt → $60–100 | ~80–120 [stima] | **[manca]** | ~0,77 | Adams-Fontaine-Ornthanalai (meccanismo); tradingstats HOD (contro) | **CANDIDATA DEBOLE**, rischio di concentrazione per anno |

Nessuna candidata su **MNQ** o **MGC**: su entrambi R/ATR è ≤ 0,37 e il costo per R del micro è il più alto (MGC) o non migliore di MYM/M2K (MNQ).

---

## 3. Schede delle candidate

Convenzioni comuni:
- Sessione RTH 9:30–16:00 ET con template di sessione dedicato in MultiCharts. Uscita a tempo sempre ≤ 15:45, ben prima del cutoff Lucid delle 16:45 ET.
- ATR14 calcolato su barre **giornaliere RTH** come data2. Tutto è in punti o in ATR, niente percentuali di prezzo, perché i continuous sono back-adjusted.
- Un trade al giorno per regola, salvo diversa indicazione.

### #1 IB-C Breakout a target fisso (MYM; M2K come replica)

- **IPOTESI.** Quando il primo periodo dopo l'IB (C, 10:30–11:00) chiude fuori dall'IB, il prezzo percorre un'altra distanza piccola e fissa nella stessa direzione prima di tornare indietro di una distanza un po' più grande.
- **PERCHÉ DOVREBBE FUNZIONARE.** Su ES 2015–2025, quando C chiude sopra l'IB high, il 79% dei giorni raggiunge un'estensione del 50% dell'IB. Senza la conferma di C, l'estensione del 100% arriva solo nel 18,8% dei giorni, e con la conferma più che raddoppia [fonte: tradingstats, descrittivo]. **Chi perde: non lo so dire con sicurezza.** L'ipotesi è che perdano i trader rotazionali (fade dell'IB secondo il market profile) che vendono la rottura. È un segnale debole e lo dichiaro.
- **REGOLE.**
  - IB = massimo e minimo 9:30–10:29:59. W = IBH − IBL.
  - Filtro: 0,25·ATR14 ≤ W ≤ 1,0·ATR14. Si escludono gli IB "extreme", dove la fonte mostra MFE:MAE < 1.
  - Segnale alla chiusura della barra delle 10:59 (oppure della barra a 30 minuti 10:30–11:00): Close(C) > IBH → long, Close(C) < IBL → short.
  - Ingresso a mercato all'open delle 11:00.
  - Stop: S = clamp(0,40·ATR14; 120; 200) punti YM. Target: T = 0,80·S.
  - Uscita a tempo alle 15:45.
- **RISCHIO PER TRADE.** MYM da 120 a 200 punti, cioè **da $60 a $100 per micro**. M2K da 12 a 20 punti, $60–100.
- **PERCHÉ RISPETTA IL PROFILO.** R:R fissato a 0,80 per costruzione. Serve WR ≥ 61,9% per PF 1,3 e ≥ 63,6% per PF 1,4. Le uscite a tempo spostano il R:R e vanno contate a parte: se superano il 15% dei trade, la forma dell'uscita non è più quella dichiarata.
- **COSA LA FALSIFICA (test di un'ora).**
  1. Numero di segnali per anno: deve essere ≥ 40 in **ogni** anno, con distanza massima fra due trade ≤ 30 giorni di calendario.
  2. P(T prima di S) a primo tocco: eccesso netto sul null del 55,6% **≥ +8 pp** in aggregato e > 0 in ogni anno.
  3. Placebo: stesso ingresso alle 11:00 con direzione casuale. Deve dare un eccesso ≈ 0, altrimenti il null è mal calibrato (drift, uscite a tempo).
  4. Se il 79% della fonte svanisce misurando dall'**ingresso** e non dall'IB high, la candidata è morta. Parte dell'estensione avviene dentro C, quindi una parte di quel 79% è guardare avanti.
- **FONTE.** tradingstats.net, *Initial Balance Breakout Statistics* (ES 2.686 giorni, NQ 2.833, dati a 1 minuto 2015–2025): https://tradingstats.net/initial-balance-breakout-statistics/. Livello **2–3**: statistiche descrittive dichiarate, senza costi, senza risoluzione a primo tocco con stop. Il tuo ORB morto su NQ (+1,5 pp) è la controprova che senza filtro l'edge è minimo.
- **COSA NON SO.** I dati per YM e RTY (la fonte copre solo ES/NQ). La distribuzione di P(T prima di S). Il drawdown. Se l'edge sopravvive dopo l'ingresso alle 11:00.

### #2 IB-C Failure → midpoint dell'IB (MYM; M2K come replica)

- **IPOTESI.** Se C buca un lato dell'IB ma chiude di nuovo dentro, il prezzo torna almeno al punto medio dell'IB prima di superare l'estremo di C.
- **PERCHÉ DOVREBBE FUNZIONARE.** Su ES il 30% dei giorni ha un C "fallito". Di questi, il 46,8% finisce per rompere anche il lato opposto dell'IB e il 37,9% chiude dentro l'IB [fonte: tradingstats]. Il midpoint sta fra i due lati, quindi viene raggiunto almeno altrettanto spesso, ma senza vincolo di stop. **Chi perde:** chi ha comprato la rottura in C ed esce in stop quando il prezzo rientra. Le sue uscite alimentano il movimento. È un meccanismo nominabile, più solido di quello della #1.
- **REGOLE.**
  - Short se High(C) > IBH, Close(C) < IBH e Low(C) > IBL. Long nel caso speculare.
  - Ingresso a mercato alle 11:00. Target: M = (IBH + IBL)/2.
  - Stop naturale: High(C) + 0,05·ATR14. La distanza S è portata ad almeno 100 punti YM; se supera 200 il trade si salta.
  - Si entra solo se T/S ∈ [0,5; 1,0]. Uscita a tempo alle 15:45.
- **RISCHIO PER TRADE.** MYM da 100 a 200 punti, **$50–100 per micro**. M2K da 10 a 20 punti, $50–100.
- **PERCHÉ RISPETTA IL PROFILO.** Il target è vicino (la metà dell'IB) e lo stop sta oltre un estremo già rifiutato. Il filtro sul R:R lo tiene in 0,5–1 per costruzione.
- **COSA LA FALSIFICA.** Lo stesso test 1.2: eccesso netto ≥ +8 pp sul null 1/(1+R:R) calcolato **trade per trade**. Poi la frequenza: se scende sotto 40 l'anno in un anno qualsiasi, da sola non regge l'inattività. In quel caso va accorpata alla #1, perché i due eventi sono mutuamente esclusivi: C chiude fuori oppure C buca e rientra.
- **FONTE.** Come la #1, livello 2–3.
- **COSA NON SO.** Le statistiche su YM/RTY, il primo tocco, il drawdown, quanti giorni vengono scartati dal filtro sul R:R.

### #3 Gap piccolo fade verso la chiusura RTH precedente (MYM; M2K; MES come controllo)

- **IPOTESI.** Un gap d'apertura piccolo che apre dentro il range del giorno prima viene richiuso entro la prima ora e mezza più spesso di quanto il rapporto target/stop richieda.
- **PERCHÉ DOVREBBE FUNZIONARE.** Su NQ 2015–2025 i gap "tiny" (< 0,3 ATR) si richiudono al 100% entro la chiusura nel 77,8% dei casi. Con apertura dentro il range precedente la percentuale è 70,4%, contro 44–47% con apertura fuori. Il 43,3% di tutti i riempimenti avviene entro le 10:30 [fonte: tradingstats]. Sul piano accademico Grant-Wolf-Yu (2005) trovano inversioni significative sui futures S&P 1987–2002 dopo grandi variazioni in apertura. **Chi perde:** chi ha fissato il prezzo nella sessione overnight sottile e chi compra o vende all'apertura. Fra le ipotesi accademiche, l'inventory degli intermediari (Boyarchenko-Larsen-Whelan) o i clienti retail overnight contro gli arbitraggisti diurni (Iwanaga-Sakemoto).
- **PERCHÉ È DEBOLE.**
  - Grant-Wolf-Yu scrivono che la significatività si riduce nettamente dopo i costi bid-ask.
  - Iwanaga-Sakemoto (2026) trovano che l'inversione overnight → prima mezz'ora si è indebolita dopo gli anni 2010. Un retest aneddotico sul 2025 chiude a −6,24%.
  - Caporale-Plastun (sullo S&P 500) trovano momentum, non riempimento, nel giorno del gap.
  - Il "93% con la prima candela da 15 minuti verso il riempimento" della fonte è **guardare avanti**: il tempo mediano di riempimento di un gap tiny è 7 minuti, quindi la condizione contiene già l'esito.
- **REGOLE.**
  - G = Open(prima barra RTH 9:30) − Close(ultima barra RTH del giorno precedente).
  - Si entra se 60 ≤ |G| ≤ 0,35·ATR14 (punti YM) e l'apertura è dentro [Low, High] RTH del giorno precedente.
  - Ingresso a mercato all'apertura, oppure a 9:31 per evitare lo slippage della stampa d'apertura (testare entrambe e dichiararlo).
  - Target: chiusura RTH precedente. Stop: S = clamp(1,3·|G|; 120; 200). Si entra solo se |G|/S ∈ [0,5; 1,0]. Uscita a tempo alle 11:00.
  - M2K: |G| ≥ 6 punti, S = clamp(1,3·|G|; 12; 20).
- **RISCHIO PER TRADE.** MYM 120–200 punti, **$60–100 per micro**. M2K 12–20 punti, $60–100.
- **PERCHÉ RISPETTA IL PROFILO.** Il target è il gap (vicino), lo stop è circa 1,3 volte il gap. Il R:R è legato al gap noto all'ingresso, con pavimento e tetto, quindi è dichiarato prima ed è conforme all'anti-pattern 3.
- **COSA LA FALSIFICA (prima del backtest).**
  1. Sui dati NQ della fonte stessa: la MAE mediana dei gap tiny è 27,8 punti e il 75° percentile 67,5. Con uno stop di 50 punti, circa un terzo dei casi tocca lo stop [stima mia, interpolazione grezza], contro un target mediano dell'ordine della dimensione del gap. Ne viene un PF dell'ordine di 1,0–1,1 [stima]. **Se su YM la tabella primo tocco conferma questo ordine di grandezza, la candidata è morta.**
  2. Il test 1.2 per anno, con attenzione al 2020 (anno di alta volatilità, in cui la fonte accademica dice che l'inversione si rafforza). Se un solo anno porta più del 50% del profitto, muore per la regola di consistenza annuale.
- **FONTI.** tradingstats gap NQ https://tradingstats.net/gap-fill-strategy/ (livello 2). Grant, Wolf, Yu 2005, JBF https://doi.org/10.1016/j.jbankfin.2004.04.006 (livello 1 per l'esistenza, ma con costi l'edge si riduce molto). Iwanaga-Sakemoto 2026 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5807282 (livello 1–2, testo completo non letto: SSRN ha bloccato l'accesso).
- **COSA NON SO.** Le statistiche dei gap su YM/RTY, il primo tocco, la dimensione mediana del gap in punti per anno, il drawdown.

### #4 VWAP fade di metà giornata (MYM principale, MES come controllo)

- **IPOTESI.** Fra le 11:00 e le 14:30 una deviazione moderata dal VWAP di sessione rientra verso il VWAP più spesso di quanto richieda il rapporto target/stop, soprattutto dal 2022 in poi.
- **PERCHÉ DOVREBBE FUNZIONARE.** Adams, Fontaine e Ornthanalai (Quantpedia ne fa una sintesi) trovano che la presenza delle 0DTE abbassa la volatilità intraday dello S&P. Una gamma netta più alta dei market maker prevede inversioni più forti dell'order flow sugli E-mini e momentum negativo ad alta frequenza, con un effetto che svanisce in circa un'ora. **Chi perde:** chi insegue il movimento a metà giornata, mentre i dealer lunghi di gamma vendono i rialzi e comprano i ribassi per coprirsi.
- **PERCHÉ È DEBOLE.**
  - (a) Lo studio tradingstats sugli estremi di sessione (NQ, ES, YM, RTY, 2019–2026) mostra che il fade senza filtro sta vicino al pareggio prima dei costi.
  - (b) Il meccanismo esiste dal 2022 (scadenze SPXW del martedì e giovedì introdotte nel 2022). Il 2020–2021 potrebbe quindi essere negativo e concentrare il profitto nel 2022–2024: rischio diretto sulla regola "nessun anno > 50%".
  - (c) Il meccanismo riguarda lo S&P. Su YM vale solo per correlazione.
- **REGOLE.**
  - VWAP ancorato alle 9:30 RTH su barre a 5 minuti con volume.
  - Segnale alla chiusura di una barra fra le 11:00 e le 14:30: D = Close − VWAP. Short se D ≥ +0,30·ATR14, long se D ≤ −0,30·ATR14. k = 0,30 è fissato a priori; 0,25 e 0,35 servono solo come test di robustezza, non per ottimizzare.
  - Filtro trend: si salta se il range di sessione al momento del segnale supera 1,0·ATR14. La fonte mostra che gli estremi oltre circa 1 ATR rientrano di rado.
  - Si saltano i giorni FOMC (lista di date in input). Un trade al giorno.
  - Target: il VWAP al momento dell'ingresso (prezzo fisso). Stop: S = clamp(1,3·|D|; 120; 200) punti YM; MES clamp(1,3·|D|; 12; 20). Si entra solo se il R:R ∈ [0,5; 1,0]. Uscita a tempo alle 15:30.
- **RISCHIO PER TRADE.** **$60–100 per micro** su entrambi.
- **PERCHÉ RISPETTA IL PROFILO.** Il target è la media (vicino) e lo stop sta a circa 1,3 volte la deviazione. R:R intorno a 0,77.
- **COSA LA FALSIFICA.** Il test 1.2 **separato per 2020–2021 e 2022–2024**. Se l'eccesso è negativo nel primo blocco e positivo nel secondo, la regola di consistenza annuale la uccide quasi certamente: il profitto si concentra in pochi anni. Se è vicino a zero in entrambi, è morta per edge assente. Va misurata prima su MYM, perché su MES il costo per R è quasi il doppio.
- **FONTI.** Sintesi Quantpedia dello studio Adams-Fontaine-Ornthanalai: https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/, PDF https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf. Livello 1 per il meccanismo (volatilità e inversioni a 10 minuti), **nessun test di strategia**. Controprova: https://tradingstats.net/high-of-the-day-hold/ (livello 2).
- **COSA NON SO.** Tutto ciò che riguarda il trade: WR, R:R realizzato, frequenza, drawdown. È la più speculativa delle quattro.

---

## 4. Le due "bloccate": come si sbloccano (non sono idee nuove)

- **VWAP Pullback.** Al posto dello stop al pivot swing si usa uno stop dichiarato S = clamp(pivot_distance; 0,15·ATR14; 0,40·ATR14), con pavimento e tetto in punti per strumento. Su MYM 60–200 punti. Si tiene un target fisso con R:R fra 0,6 e 0,9. Il 10% di stop "indistinguibili dal rumore" sparisce per costruzione. Prima di rifare il backtest su MNQ, conviene rifarlo su MYM (sezione 1.1).
- **DriftPullback.** Il drift va riscritto come (Close − Close[n]) / ATR14 invece che in percentuale. Nessun dato nuovo da parte mia: è solo la strada di sblocco che avevi già indicato.

---

## 5. Perché non ci sono quasi-candidate

Ogni idea vicina al profilo che ho trovato sforava **almeno due** vincoli. Il caso tipico: WR 53–56% e insieme PF pratico circa 1,17 con R:R circa 1, come il momentum dell'ultima mezz'ora. Per la tua regola queste idee vanno negli scarti e ce le ho messe. Non ho inventato parametri per riempire la sezione.

---

## 6. Osservazioni separate sui vincoli (i gate non li riscrivo)

1. **La regola di inattività è più blanda di come la descrive il prompt.** Lucid considera abbandonato un conto che in 30 giorni di calendario non ha fatto almeno un trade con $1 di P&L netto. Il vincolo che conta davvero, oltre al tuo "≥ 40 trade l'anno", è **la distanza massima fra due trade ≤ 30 giorni**. L'ho aggiunta ai test di falsificazione.
2. **Vincolo nuovo per i payout funded:** 5 giorni per ciclo con almeno $150 di profitto ciascuno (sul 50k) e profitto netto del ciclo positivo. Con R = $100/micro e R:R 0,8 un trade vincente vale circa $78 netti per micro, quindi **serve almeno 2 micro** per avere un giorno qualificante con un solo trade. Ma con 2 micro il tuo tetto di DD storico per micro ($1.000) diventa $2.000, cioè **l'intero MLL**. C'è una tensione strutturale fra il gate sul DD per micro e la meccanica dei payout. Va decisa a monte del backtest, non dopo.
3. **L'MLL non "si blocca a $52.100".** Trailing finché il saldo EOD non supera $52.100 (initial trail balance), poi si **blocca a $50.100**. Inoltre, sul funded, ogni richiesta di payout riporta subito l'MLL a $50.100. Il mio Monte Carlo usa questa meccanica.
4. **Cutoff flat: 16:45 ET** su LucidFlex. Nessuna candidata ne è toccata.
5. **Sulla tesi del prompt** ("cambiare strumento migliora il rischio ma peggiora il rapporto costo/movimento"): vale in tick, non al budget di R in dollari. Vedi 1.1. Il numero da misurare per primo resta la slippage reale su MYM e M2K.
6. **Se il test 1.2 fallisce su tutte e quattro**, la conclusione coerente con quello che ho letto è che il profilo PF ≥ 1,3 / WR ≥ 55% / R ≈ $100 per micro **richieda un edge di 2–4 volte superiore** a quello documentato per le famiglie intraday sugli indici. A quel punto il problema è il rapporto MLL/target del conto, non le strategie.

---

## 7. Scartate da me

| Idea | Fonte (link) | Motivo dello scarto in una riga |
|---|---|---|
| Momentum dell'ultima mezz'ora (prima mezz'ora → ultima mezz'ora) | Gao-Han-Li-Zhou 2018 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 | Uscita in chiusura (R:R ~1) con WR 53–56% → PF circa 1,17: sfora WR e PF pratico |
| Momentum dell'ultima mezz'ora (resto del giorno) su 60 futures | Baltussen-Da-Lammers-Martens 2021 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365 | Come sopra; un retest aneddotico su 1.085 sessioni SPX 2022–2026 lo trova piatto in ogni anno; concentrazione per anno quasi certa |
| Inversione overnight → prima mezz'ora con uscita alle 10:00 | Iwanaga-Sakemoto 2026 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5807282 | Uscita a tempo senza target; indebolita dopo il 2010; −6,24% in un retest aneddotico sul 2025. Assorbita nella #3 come variante con target |
| Momentum "noise area" su SPY | Zarattini-Aziz-Barbon 2024 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172 | Trend following con trailing stop: escluso dal profilo |
| Miglioramenti con ottimizzazione dei parametri della noise area | Maróy 2025 https://papers.ssrn.com/sol3/Delivery.cfm/5095349.pdf?abstractid=5095349&mirid=1 | Trend following con tutti i parametri ottimizzati e Sharpe > 3: overfitting dichiarato nel metodo |
| Long ES fra le 14:00 e le 15:00 (inventory) | Boyarchenko-Larsen-Whelan, NY Fed SR917 https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf | Gli autori stessi: Sharpe 1,1 prima dei costi, −0,5 dopo lo spread |
| Fade di ogni estremo di sessione | tradingstats https://tradingstats.net/high-of-the-day-hold/ | La fonte mostra il pareggio prima dei costi per ogni ampiezza di stop |
| Reversion Grader A+/A | stessa | Pesatura proprietaria non pubblicata (non codificabile) ed edge sottile con R:R probabilmente < 0,5–0,75 |
| Gap fill "93% con la prima candela da 15 minuti verso il riempimento" | tradingstats gap https://tradingstats.net/gap-fill-strategy/ | Guarda avanti: la condizione contiene il riempimento (mediana 7 minuti sui gap tiny) |
| Fade del gap SPY 0,15–0,6% con target al 75% | QuantifiedStrategies https://www.quantifiedstrategies.com/gap-fill-trading-strategies/ | Dati EOD Yahoo con massimi e minimi errati, ammessi dall'autore |
| Pairs intraday SPY/IWM | QuantStart https://www.quantstart.com/articles/Backtesting-An-Intraday-Mean-Reversion-Pairs-Strategy-Between-SPY-And-IWM/ | Pair trading, zero costi, look-ahead lasciato di proposito |
| Fade generico delle bande VWAP | CrossTrade https://crosstrade.io/learn/trading-strategies/vwap-reversion ; MetroTrade | Affermato senza test; la versione testabile è la #4 |
| Regole IB su YM "100% su 19 sessioni" | edgeful https://www.edgeful.com/blog/posts/ym-initial-balance-strategy | 128 sessioni e condizioni sovrapposte: campione minuscolo, overfitting |
| Gap momentum nel giorno del gap | Caporale-Plastun (citato su ResearchGate) | Tenuta direzionale fino a chiusura (profilo trend); tenuto come prova contraria alla #3 |
| Short-term reversal con futures | Quantpedia https://quantpedia.com/strategies/short-term-reversal-with-futures | Settimanale e cross-sectional: incompatibile con flat EOD |
| Mean reversion valutaria | Quantpedia https://quantpedia.com/how-to-build-mean-reversion-strategies-in-currencies/ | Ribilanciamento mensile |
| Trend intraday con 0DTE | Concretum https://concretumgroup.substack.com/p/intraday-trend-following-with-0dte | Opzioni non disponibili; trend following |
| Qualunque candidata su MGC | (analisi 1.1) | Costo micro circa 3,3% di R [stima], R ≤ 0,37 ATR; Gold Asian Range già morta per edge assente |
| Qualunque breakout su MNQ con R ≤ 55 punti | (analisi 1.1) | R = 0,12–0,21 ATR: stop dentro il rumore; anti-pattern 1 confermato con un numero |

## 8. Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| CME e broker (M2K, MGC, moltiplicatori dei micro) | M2K $5/punto con tick 0,10 = $0,50; MGC 10 oz, tick $0,10 = $1; MYM $0,50/punto; MES e M2K $5 | No, verificato |
| Help center Lucid e recensioni (inattività, payout, commissioni, drawdown) | 30 giorni con un trade da $1; 5 giorni da $150; micro a $0,50 per lato, MGC $0,80; MLL bloccato a $50.100; cutoff 16:45 ET | Sì, a ogni cambio di regole |
| SSRN/JBF: "overnight intraday reversal index futures" | Grant-Wolf-Yu 2005; Fung et al. 2000; Iwanaga-Sakemoto 2026; Della Corte et al.; Liu et al. | **Sì**: testo completo di Iwanaga-Sakemoto (SSRN bloccato) e citazioni successive a Grant 2005 non lette |
| "market intraday momentum" (Gao 2018, Baltussen 2021, QuantConnect) | Edge piccolo, WR 53–56%, piatto dopo il 2022 (aneddotico) | No per questo profilo |
| Letteratura 0DTE (Adams-Fontaine-Ornthanalai, Cboe, Dim-Eraker-Vilkov) | Meccanismo di dampening e inversioni dal 2022 | **Sì**: unico meccanismo nuovo e post-2022 per la mean reversion intraday |
| Zarattini noise area e repliche (GitHub codecat-ops, Quantitativo) | Trend following; una replica parla di "edge attualmente compresso" | No |
| tradingstats.net (IB, gap, tenuta dell'HOD) | Le statistiche descrittive migliori trovate: ES/NQ/YM/RTY a 1 minuto, MAE/MFE | **Sì**: articoli non letti su estensione dopo breakout, range della settimana d'apertura, win rate vs expectancy |
| Quantpedia "intraday mean reversion index futures" | Solo strategie multi-giorno o cross-sectional | Basso; lo screener premium non è stato consultato |
| QuantifiedStrategies (gap, momentum) | Dati EOD, qualità dichiarata scarsa | No |
| Forum (ForexFactory gap, edgeful, blog VWAP) | Aneddoti, campioni corti | No |
| stooq (download dati per misurare gli ATR) | Bloccato da verifica JavaScript | Sì, con un'altra fonte di dati: **gli ATR per anno restano da misurare** |
| **Non fatto per mancanza di tempo:** futures.io, Elite Trader, Robot Wealth, Alpha Architect, libro di Crabel (ORB + NR4/NR7 con statistiche di WR), citazioni di Google Scholar | — | **Sì, filoni aperti**, non esauriti |

## 9. Testo-istruzione trovato sul web

Non ho trovato pagine con istruzioni rivolte a me. Ho ignorato solo inviti commerciali (codici sconto, iscrizioni a newsletter o indicatori), senza conseguenze sul lavoro.
