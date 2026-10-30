# Candidate per LucidFlex 50k — ricerca del 14/10/2026

Legenda livelli di fonte: **L1** = testato con dati e costi · **L2** = testato senza costi o campione corto · **L3** = affermato.
Tutti i numeri marcati *(stima)* sono miei e vanno misurati; quelli marcati *(mancante)* non li ho.

---

## 0. In sintesi

1. **Il vincolo che morde davvero non è "$500 per trade".** I vostri stessi gate sul drawdown (storico < $1.000, MC95 < $2.000 per micro) impongono una **perdita media per micro di circa $100–135** con un profilo WR 60% / PF 1,2–1,5. Il gate dei $500 è ridondante: chi passa i gate DD lo passa automaticamente.
2. **Il pavimento dei costi impone un minimo** allo stesso numero. Ne esce una **finestra** stretta per lo stop: su MES ~15–20 punti a PF 1,2; **su MGC a PF 1,2 la finestra è vuota** (spiega strutturalmente la morte della Gold Asian Range).
3. Su MYM e M2K la finestra è la più larga in unità di ATR (0,2–0,6 ATR): avevate ragione a guardare lì, ma il motivo è il **valore in dollari dell'escursione giornaliera per micro**, non i "1.000 punti Dow". MYM e M2K muovono circa 0,4× un MNQ in dollari al giorno *(stima)*.
4. Candidate: **2 vere** (IB Retest Continuation, Fade del gap piccolo), **1 condizionale** che si falsifica in un'ora con numeri che avete già (porting ORB/VaultBreak su MYM/M2K), **1 debole** (Fade dentro la Noise Area), **1 quasi-candidata sulla frequenza** (Rientro in Value Area → VPOC). **Nessuna su MNQ o MGC.**

---

## 1. Verifiche preliminari

- **Specifiche CME verificate**: MES $5/punto, M2K $5/punto, MNQ $2/punto, MYM $0,50/punto (tick = 1 punto = $0,50). MES tick $1,25; MNQ, MYM, M2K tick $0,50; MGC tick $1. La vostra colonna $/punto è corretta.
- **Range giornalieri: NON verificati online.** Uso stime a memoria per il 2020–2024 (ATR14 giornaliero RTH, media): ES ~60, YM ~420, RTY ~40, NQ ~260, GC ~30 $/oz. **Attenzione all'oro**: i "~90 punti" della vostra tabella sono coerenti con l'oro di oggi (~$4.100), non con il 2020–2024 (prezzo $1.600–2.700). È esattamente l'anti-pattern 2 applicato alla tabella stessa. Prima azione domani: calcolare l'ATR14 RTH per anno su @ES, @YM, @RTY, @NQ, @GC in MultiCharts e sostituire le mie stime.
- **Lucid** (fonti secondarie, da confermare sull'help center): target $3.000 e MLL $2.000 confermati; consistenza 50% in eval confermata. Due punti da ricontrollare: (a) le fonti descrivono l'MLL che **si blocca a saldo iniziale + $100 (cioè $50.100) quando il saldo supera $52.100**, non "si blocca a $52.100"; (b) nel funded LucidFlex il payout richiede **5 giorni con almeno $150 di profitto** sul 50K, e si parte con 2 mini (20 micro).

---

## 2. Il numero che cambia la ricerca: la finestra dello stop per micro

Metodo (script in `scripts/`): Monte Carlo con riordinamento su trade i.i.d., WR 60%, 200–300 trade (= 5 anni a 40–60/anno), 20.000 simulazioni. Unità = perdita media S.

| Profilo | DD mediano | DD 95° pct | S max per DD mediano < $1.000 | S max per DD95 < $2.000 |
|---|---|---|---|---|
| WR 60%, R:R 0,80 (PF 1,20) | 9–11 S | 18–20 S | ~$95–110 | ~$100–110 |
| WR 60%, R:R 0,90 (PF 1,35) | 8–9 S | 15–16 S | ~$110–125 | ~$123–135 |
| WR 60%, R:R 1,00 (PF 1,50) | 7–8 S | 13–14 S | ~$125–143 | ~$143–154 |

Serie perdenti più lunghe attese su 250 trade: mediana 5–6, 95° pct 8–9.

Pavimento costi: con edge netto per trade = k·S (k = 0,08 a PF 1,2; 0,14 a PF 1,35; 0,20 a PF 1,5) e le vostre soglie (netto ≥ $7 per MNQ = $70/NQ ÷ 10; ≥ $14 per MGC; per ES solo "lordo ≥ 3× costo", cioè netto ≥ 2c), si ottiene S_min = soglia / k. Costo per micro = vostro costo big ÷ 10 (**ipotesi ottimistica**: le commissioni dei micro non scalano a 1/10). Per YM e RTY **il costo non me l'avete dato**: ho usato quello di ES, marcato come ipotesi.

| Micro | PF 1,20 | PF 1,35 | PF 1,50 |
|---|---|---|---|
| MNQ | $88–100 = 44–50 pt (0,17–0,19 ATR) | $50–118 = 25–59 pt | $35–135 = 18–68 pt |
| MES | $75–100 = 15–20 pt (0,25–0,33 ATR) | $43–118 = 9–24 pt | $30–135 = 6–27 pt |
| **MGC** | **VUOTA** (min $175 > max $100) | $100–118 = 10–12 pt | $70–135 = 7–14 pt |
| MYM *(costo ipotizzato)* | $75–100 = 150–200 pt (0,36–0,48 ATR) | $43–118 = 86–236 pt (0,20–0,56 ATR) | $30–135 = 60–270 pt |
| M2K *(costo ipotizzato)* | $75–100 = 15–20 pt (0,38–0,50 ATR) | $43–118 = 9–24 pt (0,21–0,59 ATR) | $30–135 = 6–27 pt |

Conseguenza operativa: **ogni candidata va prima confrontata con questa finestra**, non con i $500. Tutte le candidate sotto hanno lo stop dichiarato dentro la colonna PF 1,35.

Passaggio dell'eval (simulazione, trade i.i.d., MLL trailing per trade, lock a +$100): con rischio di conto $200 per trade e PF 1,35 → P(pass) ~87%, ~83 trade mediani al target; a $500 per trade → ~56%. **La frequenza è la leva del tempo, il rischio per trade è la leva della probabilità.**

---

## 3. Tabella di sintesi (migliore → peggiore)

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato (pt → $/micro) | n/anno attesi | WR atteso | R:R | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| 1 | IB Retest Continuation | MYM, M2K, MES · 1 min | Continuazione su pullback, target fisso | clamp(0,45·IB) in MES 9–24 / MYM 90–236 / M2K 9–24 → $45–120 | 100–150 *(stima)* | 55–65% *(stima derivata)* | 0,8 | tradingstats IB breakout + retest (L2, solo ES/NQ) | **CANDIDATA** |
| 2 | Fade del gap piccolo (ATR) | MES, MYM, M2K · 1 min | Fade gap apertura | 1,5×gap; MES 9–24 / MYM 90–236 / M2K 9–24 → $45–120 | 40–80 *(stima, frequenza da misurare)* | 64–72% *(stima)* | 0,67 | tradingstats gap (L2), Grant-Wolf-Yu (L1, negativo dopo costi) | **CANDIDATA** |
| 3 | Porting ORB / VaultBreak @NQ → MYM/M2K, target fisso | MYM, M2K · come l'originale | Breakout con target fisso | stop originale in ATR × ρ≈0,4 *(stima)* | come l'originale | ignoto su YM/RTY | 0,8–1,0 | i vostri dati (L1 interno) | **CANDIDATA CONDIZIONALE** |
| 4 | Fade dentro la Noise Area | MES, MYM, M2K · 1 min | Mean reversion su estremi superficiali | 0,5·σ(t), filtrato nella finestra → $45–118 | 80–150 *(stima)* | 55–65% *(stima)* | 0,8 | tradingstats HOD (L2), Zarattini (L1 per il lato opposto) | **CANDIDATA DEBOLE** |
| 5 | Rientro in Value Area → VPOC | MES, MYM, M2K · 30 min + 1 min | Mean reversion verso VPOC | fisso MES 15 / MYM 150 / M2K 15 → $75 | 30–60 *(stima)* | 60–70% *(stima)* | 0,5–1,0 | tradingstats session open (L2), forum (L3) | **QUASI-CANDIDATA (frequenza 0,75–1,5× del minimo)** |

Nessuna candidata su MNQ o MGC: vedi sezione 5.

---

## 4. Schede

### #1 — IB Retest Continuation (IBRC)

- **IPOTESI**: dopo la prima rottura dell'Initial Balance con un'estensione *poco profonda*, il primo ritorno sul livello rotto tiene e il prezzo fa un nuovo estremo.
- **PERCHÉ / CHI PERDE**: chi shorta il ritest aspettandosi il falso breakout, e chi è entrato sul breakout e viene stoppato sul pullback. **Controparte debole**: non c'è un flusso strutturale (hedging, ribilanciamento) identificabile. Possibile legame con il gamma dei dealer, ma non abbiamo quei dati.
- **REGOLE** (long; short speculare; orari ET):
  - IB = 09:30–10:29:59; R = IBH − IBL. ATR14 = ATR giornaliero RTH in **punti**.
  - Filtro: 0,15·ATR14 ≤ R ≤ 0,50·ATR14.
  - Il primo lato violato dopo le 10:30 decide la direzione (alto → solo long).
  - Il prezzo deve raggiungere IBH + 0,10R. Se prima di ritornare su IBH + 0,02R supera IBH + 0,30R → giornata scartata (estensione profonda).
  - Ingresso: limit buy a IBH + 0,02R, valido fino alle 13:30. Massimo 1 trade al giorno.
  - Stop: S = clamp(0,45R; pavimento; tetto) sotto l'ingresso. Pavimento/tetto: MES 9/24 pt, MYM 90/236 pt, M2K 9/24 pt.
  - Target: T = 0,8·S. Uscita a tempo: 15:45.
- **RISCHIO PER TRADE**: MES 9–24 pt = $45–120; MYM 90–236 pt = $45–118; M2K 9–24 pt = $45–120. Con R ≈ 0,3 ATR *(stima)* lo stop strutturale (≈0,13 ATR) cade spesso sul pavimento: in pratica è uno stop quasi fisso.
- **PROFILO**: R:R 0,8 per costruzione. WR richiesto ≥ 60% per PF 1,2 lordo. La fonte dà: rottura IB nel 96–98% dei giorni; con estensione bassa (1.1) i ritest continuano nel 71% dei casi e invertono nel ~16% (quindi ~82% condizionato al ritest); il primo ritorno resta entro il 10% di R dal livello nel ~90% dei casi; la seconda gamba aggiunge una mediana di 0,45R (NQ) / 0,56R (ES). Il target (≈0,36R sopra l'ingresso) richiede una nuova gamba di 0,1–0,2R oltre il massimo precedente → **WR 55–65%** *(stima mia)*.
- **COSA LA FALSIFICA** (un'ora su 1 min 2020–2024, ES/YM/RTY): contare i giorni che soddisfano il setup e calcolare l'esito *first-touch* (T prima di S). Muore se: (a) WR first-touch < WR_min = (S + 3c)/(T + S) — con c = costo per micro; (b) setup < 40/anno; (c) un anno vale > 50% del lordo. Seconda misura: quota di trade in cui lo stop è dettato dal pavimento.
- **FONTE**: tradingstats.net, *Initial Balance Breakout Statistics* e *Initial Balance Retest* (ES e NQ 2015–2025; descrittivo, senza costi) → **L2**. https://tradingstats.net/initial-balance-retest-statistics/
- **COSA NON SO**: esito first-touch con i miei T/S; comportamento su YM e RTY (la fonte copre solo ES/NQ); DD per contratto; stabilità 2020–2024 rispetto al 2015–2019.

### #2 — Fade del gap piccolo, normalizzato in ATR

- **IPOTESI**: un gap d'apertura piccolo rispetto all'ATR, con apertura dentro il range del giorno prima, si chiude in mattinata.
- **PERCHÉ / CHI PERDE**: lo squilibrio d'apertura (ordini overnight/MOO, posizionamento overnight su notizie minori) paga chi fornisce liquidità all'apertura. È la lettura "overreaction" di Grant-Wolf-Yu. Controparte **media**: identificabile ma sottile.
- **REGOLE** (ET):
  - G = Open RTH (prima barra 09:30) − Close RTH precedente (16:00). Tutto in punti (niente %: dati back-adjusted).
  - Condizioni: apertura dentro [Low, High] RTH del giorno prima; |G| ≤ 0,30·ATR14; 1,5·|G| dentro la finestra → |G| fra MES 6–16 pt, MYM 60–157 pt, M2K 6–16 pt.
  - Ingresso: a mercato alla chiusura della barra 09:30–09:31, contro il gap. Se il gap si è già chiuso nel primo minuto → nessun trade.
  - Target: Close precedente (chiusura 100%). Stop: 1,5·|G| dall'ingresso, fissato all'ingresso. Uscita a tempo: 11:30.
  - **Variante B** (da testare separatamente): apertura fuori dal range precedente con |G| ≤ 0,5·ATR → target = estremo precedente (High per gap up, Low per gap down), stop fisso a metà finestra.
- **RISCHIO PER TRADE**: MES 9–24 pt = $45–120; MYM 90–236 pt = $45–118; M2K 9–24 pt = $45–120.
- **PROFILO**: R:R nominale 0,67 (un po' meno se il primo minuto va verso il fill). WR richiesto ≥ 64% (PF 1,2) / ≥ 67% (PF 1,35). Fonte: gap "tiny" (< 0,3 ATR) chiusi entro la chiusura nel 77,8% su NQ, *senza stop*; la maggior parte dei fill avviene nella prima ora.
- **COSA LA FALSIFICA**: (1) distribuzione di |G|/ATR 2020–2024 → giorni nella banda ≥ 40/anno (**se no, muore subito per frequenza**); (2) first-touch: prior close prima di 1,5·|G| contro, entro le 11:30 → ≥ 64% lordo; (3) nessun anno > 50%.
- **FONTE**: tradingstats *Gap Fill Strategy* (NQ 2015–2025, senza costi né stop) → **L2**; tradingstats *When do gaps fill* (ES/NQ 2020–2025) → **L2**; mypivots *Fading the Gap* (ES, campione vecchio, senza commissioni; gli stop peggiorano il risultato) → **L2**; Grant-Wolf-Yu 2005 (S&P futures 1987–2002: inversioni significative che si riducono nettamente con un proxy dei costi) → **L1, risultato negativo dopo i costi**.
- **COSA NON SO**: WR first-touch con stop; dati per YM e RTY (la fonte gap è NQ; lo studio session-open copre tutti e quattro ma in termini di tocco); frequenza esatta nella banda.

### #3 — Porting ORB @NQ / VaultBreak @NQ → MYM/M2K con target fisso

- **IPOTESI**: la logica che su @NQ aveva edge ma DD troppo alto mantiene l'edge, in unità di ATR, su YM/RTY, dove un micro vale circa il 40% in dollari.
- **PERCHÉ / CHI PERDE**: lo stesso meccanismo dell'originale. Rischio specifico: YM potrebbe avere meno momentum d'apertura di NQ (la fonte trova NQ "più pulito" di ES nei breakout; YM non misurato).
- **REGOLE**: identiche alle vostre, con **tutte le distanze espresse in ATR14 dello strumento**, tetto e pavimento in punti presi dalla finestra (MYM 86–236, M2K 9–24). Se l'originale lascia correre: target fisso 0,8–1,0 × stop.
- **RISCHIO PER TRADE**: stop originale (in ATR) × ATR dello strumento. Rapporto in dollari ρ = (ATR_YM × 0,5) / (ATR_NQ × 2) ≈ 0,40 *(stima)*; M2K ≈ 0,38 *(stima)*. DD scalati: ORB MC95 $3.121 → ~$1.250; VaultBreak $3.109 → ~$1.250 (sotto $2.000); NQ First5 storico $5.784 → ~$2.300 (sopra $1.000: non portarla, ed è comunque DayHold = profilo trend).
- **COSA LA FALSIFICA** — **un'ora, senza nuovo backtest**: trade medio LORDO per NQ × ρ / 10 ≥ 3 × costo per micro. Con c = $3 serve un lordo NQ ≥ ~$225 per contratto. **Se il lordo NQ dell'ORB o del VaultBreak è sotto ~$225, il porting è morto prima di partire**: l'edge scala con ρ, i costi per micro no. Solo se passa: rilanciare la logica su YM/RTY e verificare che l'edge esista in ≥ 4 anni su 5.
- **FONTE**: le vostre pipeline (**L1 interno**). Evidenza esterna contraria: Mesfin 2026 (14 famiglie OHLCV su MNQ 2021–2025, ORB incluso, nessuna passa con 2 punti di costo andata-ritorno) → **L1**.
- **COSA NON SO**: il vostro trade medio lordo NQ; l'ATR reale degli strumenti; il costo reale MYM/M2K.

### #4 — Fade dentro la Noise Area (estremi superficiali)

- **IPOTESI**: uno scostamento dall'apertura **più piccolo** del movimento tipico per quell'ora rientra; oltre il confine tipico parte il momentum. Si opera solo dentro il confine.
- **PERCHÉ / CHI PERDE**: chi chiede liquidità all'interno del rumore normale paga il rientro dell'inventario dei market maker. **Controparte debole**, e la letteratura dice che a orizzonte di minuti questa inversione esiste ma è piccola rispetto ai costi.
- **REGOLE** (ET):
  - σ(t) = media sugli ultimi 14 giorni di |Close al minuto t − Open RTH| **in punti**.
  - Operativo solo se 0,5·σ(t) cade nella finestra (MES 9–24, MYM 86–236, M2K 9–24): questo è il tetto/pavimento richiesto dall'anti-pattern 2.
  - Ingressi 10:00–13:30, primo tocco per lato al giorno: limit long a Open − 0,5σ(t). Short speculare, **da testare separatamente** (la fonte trova che i minimi rientrano più dei massimi).
  - Stop: Open − 1,0σ(t) (il confine di Zarattini) → S = 0,5σ. Target: Open − 0,1σ → T = 0,4σ (R:R 0,8). Stop a tempo: 60 minuti; flat alle 15:50.
- **RISCHIO PER TRADE**: $45–118 per costruzione (filtro). Con σ a metà mattina ≈ 0,3 ATR *(stima)* lo stop è ≈ 0,15 ATR: MES ~9 pt = $45 (bordo inferiore); su MYM/M2K il filtro scarterà molti giorni a bassa volatilità.
- **PROFILO**: R:R 0,8; WR richiesto ≥ 60%. La fonte trova che allargare lo stop alza il WR ma lascia l'aspettativa vicino al pareggio *prima dei costi*. Il sottoinsieme migliore (modello proprietario) arriva a ~70% target-prima-dello-stop su NQ, con due serie di 9 perdite in sei anni.
- **COSA LA FALSIFICA**: first-touch su 2020–2024 per sola profondità/ora/lato. Muore se il lordo per trade < 3c, o se il segno cambia fra anni. Seconda misura: i tocchi di 1,0σ devono proseguire più spesso di quanto rientrino (coerenza con Zarattini); se non lo fanno, il confine è mal definito.
- **FONTE**: tradingstats *How Often Does the High of the Day Hold?* (NQ/ES/YM/RTY 2019–2026, first-touch, senza costi; il grader è proprietario) → **L2**. https://tradingstats.net/high-of-the-day-hold/ · Zarattini-Aziz-Barbon 2024 (SPY, costi dichiarati, lato momentum) → **L1** come confine. Safari-Schmidhuber 2025 → **L1 negativo** a scala di minuti.
- **COSA NON SO**: quali condizioni del grader portino davvero il segnale; R:R realizzato; costi.

### #5 — Rientro in Value Area → VPOC — **QUASI-CANDIDATA (frequenza)**

- **Vincolo sforato**: frequenza stimata 30–60/anno contro 40 = **0,75–1,5×**. È lo sforamento più grave: va misurato prima di tutto.
- **IPOTESI**: se l'apertura è fuori dalla value area precedente e il prezzo rientra e ci resta per due periodi da 30 minuti, raggiunge il VPOC.
- **CHI PERDE**: chi apre "initiative" fuori valore e non viene seguito. Debole.
- **REGOLE**: profilo TPO RTH del giorno prima (periodi da 30 min; bin ES 1 pt, YM 5 pt, RTY 0,5 pt; VA = 70% intorno al POC). Condizione: Open RTH fuori dalla VA. Trigger: due barre da 30 min consecutive chiuse dentro la VA → ingresso alla chiusura della seconda. Target: VPOC (non il lato opposto della VA). Stop fisso: MES 15 / MYM 150 / M2K 15 pt = $75. Se la distanza dal VPOC non è fra 0,5S e 1,0S → nessun trade. Flat alle 15:45.
- **COSA LA FALSIFICA**: (1) conteggio setup 2020–2024 < 40/anno → scarto; (2) first-touch con stop. Attenzione: l'81–84% della fonte **non impone l'ordine** (il VPOC può essere toccato *prima* del VAH), quindi è gonfiato rispetto al trade.
- **FONTE**: tradingstats *Session Open Analysis* (NQ/ES/YM/RTY 2014–2026, statistiche di tocco) → **L2**; nexusfi, utente che non riesce a replicare l'"80% rule" → **L3**.
- **COSA NON SO**: frequenza reale; esito first-touch; differenze TPO vs volume profile.

---

## 5. Candidate scartate (una riga)

- **Qualunque candidata su MGC a PF < ~1,35**: finestra vuota (sezione 2).
- **MNQ intraday OHLCV su barre 5 min**: Mesfin 2026, lordo 0,07–1,5 punti per trade contro 2 di costo, su 14 famiglie.
- **Gao et al. — momentum dell'ultima mezz'ora**: ~2,6 bp/giorno ≈ 1,3 pt ES ≈ $65 lordi contro $30 (2,2×); uscita alla chiusura, senza target; WR attorno a 50–55%.
- **Baltussen et al. — intraday momentum da hedging**: il condizionamento richiede il gamma (dati che non abbiamo); uscita alla chiusura.
- **Zarattini-Aziz-Barbon — Noise Area momentum**: trend following con trailing stop; profilo escluso (usata solo come confine nella #4).
- **Maróy 2025 — Noise Area ottimizzata (Sharpe > 3)**: tutti i parametri ottimizzati; famiglia trend.
- **Grant-Wolf-Yu — fade dei grandi movimenti d'apertura**: significatività ridotta dai costi secondo gli autori; i dati moderni dicono che gli estremi profondi non rientrano.
- **Fade dei gap grandi (> 1,2 ATR)**: chiusura dell'8,2%.
- **Gap continuation sui gap grandi**: ~5% dei giorni (≈13/anno); Mesfin N = 22.
- **Asia range sweep → reversion (indici)**: statistica di tocco senza stop, liquidità notturna dei micro, struttura gemella della Gold Asian Range (morta per causa A).
- **VWAP 2σ band fade come strategia autonoma**: solo affermazioni (L3); fusa come variante della #4.
- **Stagionalità prima/ultima mezz'ora ES**: +1,8/+2,1 bp ≈ 1 pt ES ≈ $50 < 3×$30; nessun target; autore non identificato.
- **"80% rule" classica (target = lato opposto della VA)**: R:R tipicamente > 1, fuori profilo.
- **ORB su NQ "74,5% WR, PF 2,51" (tradealgo)**: affermazione senza fonte, su @NQ.
- **Reversion a scala di minuti (Safari-Schmidhuber; Carver)**: gli autori la dicono non sfruttabile dopo i costi, se non con limit order e costi minimi.
- **Reversion Grader tradingstats (A+/A)**: modello proprietario, non codificabile.
- **FOMC pre-announcement drift**: 8 eventi/anno (scartata in 10 secondi).

---

## 6. Osservazioni separate sui gate (non li modifico)

1. **Gate 1 ($500 per micro) è ridondante** rispetto ai gate DD. Il numero da guardare per primo è la perdita media per micro: ~$100–135.
2. **Costi dei micro**: sviluppare sul big e dividere per 10 sottostima i costi reali dei micro (le commissioni per contratto non scalano a 1/10). Con costi micro reali più alti, la finestra della sezione 2 si restringe dal basso. **Serve il costo reale per micro di MES/MYM/M2K/MNQ/MGC** sulla piattaforma Lucid.
3. **Soglie di costo mancanti per YM e RTY**: senza, le candidate su MYM/M2K usano un'ipotesi.
4. **Pass dell'eval**: la frequenza è la leva più forte. A PF 1,35 e $200 di rischio di conto per trade servono ~80 trade: a 40 trade/anno sono due anni, a 150/anno circa sei mesi.
5. **Payout funded**: servono giorni da ≥ $150; con perdita media ~$100 per micro e 1 trade/giorno servono 2–4 micro, e i DD per micro vanno moltiplicati di conseguenza contro l'MLL di $2.000.

---

## 7. Memoria — da incollare

### 7.1 Scartate da me

| Idea | Fonte (link) | Motivo dello scarto in una riga |
|---|---|---|
| Intraday momentum ultima mezz'ora (Gao, Han, Li, Zhou) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 | ~$65 lordi per ES contro $30 di costo (2,2×), uscita alla chiusura senza target, WR ~50–55% |
| Intraday momentum da hedging gamma (Baltussen, Da, Lammers, Martens) | https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598 | richiede dati gamma/opzioni; uscita alla chiusura |
| Noise Area momentum (Zarattini, Aziz, Barbon) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172 | trend following con trailing: profilo escluso (riusata come confine nella #4) |
| Noise Area ottimizzata, Sharpe > 3 (Maróy) | https://papers.ssrn.com/sol3/Delivery.cfm/5095349.pdf?abstractid=5095349&mirid=1 | ottimizzazione di tutti i parametri + famiglia trend |
| Fade dei grandi movimenti d'apertura (Grant, Wolf, Yu 2005) | https://researchwith.montclair.edu/en/publications/intraday-price-reversals-in-the-us-stock-index-futures-market-a-1/ | gli autori stessi: significatività ridotta dai costi; campione fino al 2002 |
| Fade gap grandi (> 1,2 ATR) | https://tradingstats.net/gap-fill-strategy/ | fill same-day 8,2% |
| Gap continuation su gap grandi | https://arxiv.org/abs/2605.04004v1 | ~13 giorni/anno; nello studio N = 22 |
| 14 segnali OHLCV intraday su MNQ (ORB, gap, volume, Asia...) | https://arxiv.org/abs/2605.04004v1 | lordo 0,07–1,5 pt/trade contro 2 pt di costo: nessuno passa |
| Asia range sweep & reversion su indici | https://tradingstats.net/asia-range-cascade-12-year-backtest/ | statistica di tocco senza stop; liquidità notturna; gemella della Gold Asian Range (A) |
| VWAP 2σ band fade (blog vari) | https://www.futureshive.com/blog/vwap-trading-strategy-futures-2025 | solo affermazioni (L3), numeri senza metodo; fusa nella #4 |
| Stagionalità prima/ultima mezz'ora ES | https://quanttraderjournal.com/articles/intraday-seasonality-futures | ~1 pt ES/giorno < 3× costo; senza target; autore ignoto |
| "80% rule" classica (target = lato opposto VA) | https://ftmo.com/en/blog/market-profile-master-the-80-trading-strategy-hidden-magnets/ | R:R > 1, fuori profilo; replica fallita sul forum |
| ORB NQ "74,5% WR, PF 2,51" | https://www.tradealgo.com/trading-guides/futures/futures-trading-strategies | affermazione senza fonte, su @NQ |
| Reversion a 2–30 minuti | https://arxiv.org/abs/2501.16772 · https://qoppac.blogspot.com/2025/03/very-slow-mean-reversion-and-some.html | non sfruttabile dopo i costi con barre e ordini a mercato |
| Reversion Grader A+/A | https://tradingstats.net/high-of-the-day-hold/ | modello proprietario non codificabile (si usano solo le leve pubbliche) |
| Qualunque candidata MGC a PF < 1,35 | (aritmetica, sezione 2) | finestra dello stop vuota |
| FOMC pre-announcement drift | — | 8 eventi/anno: inattività |
| NQ First5 portata su MYM | (aritmetica, #3) | DD storico scalato ~$2.300 > $1.000, e profilo DayHold |

### 7.2 Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| CME / NinjaTrader / quantvps — specifiche micro | moltiplicatori e tick verificati | No (chiuso) |
| Lucid — help center + guide secondarie | regole eval; MLL lock a $50.100; payout 5 giorni ≥ $150 | Sì: verificare sull'help center ufficiale (lock MLL, allowed trading times) |
| tradingstats.net — gap fill (NQ), gap timing (ES/NQ) | fill rate per dimensione ATR, MAE, timing | **Sì**: manca la versione YM/RTY e il first-touch con stop |
| tradingstats.net — IB breakout + IB retest | statistiche ritest/continuazione per livello di estensione (ES/NQ) | **Sì, filone più promettente**; manca YM/RTY |
| tradingstats.net — High of the day hold | depth/tempo/lato; WR vs R:R al variare dello stop | Sì, per le leve pubbliche |
| tradingstats.net — session open / VA / VPOC | tocchi per tipo di apertura su 4 indici | Parziale: solo tocchi, senza ordine |
| tradingstats.net — ORB (ES/NQ), Asia range | continuazioni, double break | Basso |
| SSRN/arXiv — Mesfin 2026 (MNQ falsification) | risultato negativo sistematico su MNQ | Sì come metodo; chiude MNQ intraday OHLCV |
| SSRN — Gao et al.; Baltussen et al. | momentum ultima mezz'ora | No (costi e profilo) |
| SSRN — Zarattini-Aziz-Barbon; Maróy | Noise Area momentum | No come strategia; sì come confine |
| JBF — Grant-Wolf-Yu 2005 (+ citanti) | reversal dopo grandi aperture, negativo dopo i costi | Basso; i citanti non sono stati seguiti (tempo) |
| arXiv — Safari-Schmidhuber 2025; blog Carver | regimi trend/reversion per orizzonte | No (chiuso per i nostri costi) |
| Quantpedia (ricerca generica mean reversion) | nulla di intraday su indici futures | **Non esplorato a fondo**: ripassare con query "intraday" e "opening" |
| Blog VWAP / 80% rule / forum nexusfi | affermazioni (L3), un tentativo di replica fallito | No |
| mypivots — Fading the Gap (ES) | vecchio studio, gli stop peggiorano | No |
| **Non visitati (tempo finito)** | Alpha Architect, Robot Wealth, QuantConnect, Elite Trader, NBER, Scholar | **Sì**: aperti per tempo, non esauriti |

---

## 8. Prompt injection

Nessuna pagina consultata conteneva istruzioni rivolte a me. Ho trovato solo testo promozionale rivolto ai lettori (es. "Reversion Grader" su tradingstats, offerte "Pro" su tradealgo): ignorato.
