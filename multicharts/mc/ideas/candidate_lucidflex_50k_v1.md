# Strategie candidate – LucidFlex 50k (eval + payout)

Data: 14/10/2026. Documento di **proposta e verifica dei vincoli**, non un backtest. Nessuna strategia qui sotto è stata backtestata da me su @NQ/@ES/@GC. Tutti i WR, gli R:R e i n/anno sono **stime a priori**, segnalate come tali.

---

## 0. Verifica di fattibilità dei gate (calcolata da me, Monte Carlo su Bernoulli i.i.d.)

Prima di proporre qualsiasi cosa ho controllato se il profilo richiesto (WR≥55%, R:R 0,5–1, PF≥1,2) è compatibile con i limiti di drawdown per micro. 4.000 simulazioni per riga, perdita = −1R, vincita = +R:R. "DD" = drawdown massimo su n trade, in multipli di R.

| WR | R:R | PF | n trade | E[R]/trade | DD mediano | DD 95° |
|---|---|---|---|---|---|---|
| 0,60 | 0,80 | 1,20 | 300 | 0,080 | 10,6R | 20,4R |
| 0,60 | 0,80 | 1,20 | 600 | 0,080 | 13,4R | 24,2R |
| 0,60 | 0,87 | 1,30 | 250 | 0,120 | 9,1R | 16,5R |
| 0,62 | 0,86 | 1,40 | 250 | 0,153 | 8,0R | 14,0R |
| 0,62 | 0,86 | 1,40 | 500 | 0,153 | 9,5R | 16,5R |
| 0,65 | 0,81 | 1,50 | 250 | 0,177 | 7,0R | 12,3R |

**Cosa ne segue (vale per tutte le candidate):**

1. **Lo stop vero è molto più stretto del tetto nominale.** Per avere DD 95° < $2.000 e DD storico < $1.000 per micro serve **R ≈ $100–130 per micro**, cioè circa **MNQ 50–65 pt, MES 20–26 pt, M2K 20–26 pt, MGC 10–13 pt**. I tetti 250/100/100/50 non sono mai il vincolo che stringe: stringe il drawdown.
2. **Con PF 1,2 i gate non si possono soddisfare tutti insieme.** Con R=$100/micro (MNQ 50 pt), a PF 1,2 il lordo atteso è 0,08×50 = 4 pt = $80 per mini; tolti $15 restano $65, sotto la soglia di $70. Allargare lo stop per aumentare il netto sfonda il DD. **In pratica serve PF ≥ ~1,35–1,4.** Questo l'ho calcolato, non l'ho stabilito io come regola. Il gate formale resta PF≥1,2 (vedi nota §4).
3. **Gate costi per strumento con PF 1,4 (E≈0,15R):** NQ R=55 pt, lordo ≈ 8,3 pt ≈ $165, netto ≈ $150 ≥ $70 ✔. ES R=22 pt, lordo ≈ $165, netto ≈ $135 ≥ $90 ✔. GC R=11 pt, lordo ≈ $165, netto ≈ $140, **esattamente sulla soglia** ✖/✔. Su GC il gate costi è il più difficile.
4. Il modello i.i.d. **sottostima** i drawdown reali, perché le serie di perdite si concentrano nei regimi trend. I numeri sopra sono un **limite inferiore**.

---

## 1. Tabella di sintesi (dalla migliore alla peggiore)

| # | Nome | Strumento·TF | Famiglia | Stop dichiarato (pt → $/micro) | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fade del gap piccolo alla chiusura precedente | MNQ (alt. MES) · 5m RTH | Mean reversion (gap fill) | MNQ 55 pt → $110 (MES 22 → $110) | 80–120 | 60–68% (stima) | 0,5–0,9 (variabile, target strutturale) | Statistiche descrittive NQ 2015–2025 (non è un trade test) | **Sopravvive su carta.** Priorità 1 per il test |
| 2 | Fade dell'estremo di sessione poco profondo | MES/MNQ · 5m RTH | Mean reversion (estensione dall'open in ATR) | MES 22 pt → $110 / MNQ 55 → $110 | 100–200 | 58–65% (stima) | 0,6–0,9 | Statistiche descrittive 2019–2026 su 4 indici (non è un trade test) | **Sopravvive su carta** |
| 3 | Ritorno all'open settimanale (Mar–Ven, intraday) | MNQ/MES · 15m RTH | Mean reversion (livello di riferimento settimanale) | MNQ 55 pt → $110 | 45–70 | 60–70% (stima) | 0,5–0,9 | Statistiche descrittive su 565 settimane NQ (tocco su 4 giorni, non intraday) | **Sopravvive, con riserva** su n e su costi |
| 4 | Sweep fallito di PDH/PDL | MES · 5m RTH | Reversal (stop-run fallito) | MES 22 pt → $110 | 60–100 | 55–62% (stima) | 0,7–1,0 | Solo affermazioni da blog, nessun test | **Sopravvive su carta**, evidenza debole |
| 5 | Fade della banda VWAP ±2σ con target limitato | MES · 5m RTH 10:00–15:00 | Mean reversion (VWAP) | MES 22 pt → $110 | 80–150 | 58–65% (stima) | 0,6–0,9 | Solo affermazioni commerciali ("75–80%"), nessun test | **Sopravvive su carta**, evidenza debole |
| 6 | Fade della prima uscita dal range overnight sull'oro | MGC · 5m 08:20–12:00 ET | Mean reversion (range) | MGC 12 pt → $120 | 80–150 | ignoto | 0,6–0,9 | **Nessuna fonte trovata.** È un'ipotesi | **Marginale**: gate costi GC al limite, fonte assente |
| 7 | Fade del falso breakout dell'OR a 30 min | MES · 5m RTH | Reversal (failed breakout) | MES 22 pt → $110 | 60–100 | ignoto | 0,7–1,0 | Indiretta: uno studio MNQ non trova edge nei breakout OHLCV. Non dimostra l'edge del fade | **Marginale.** Su NQ escluso: rischio di ricadere nella famiglia "breakout NQ" |

Considero "serie" le **#1–#5**. La #6 e la #7 sono riempitivi onesti con evidenza minima, utili come varianti di diversificazione da testare per ultime. **Nessuna candidata ha oggi prove testate che rispettino i gate.** Il verdetto "sopravvive" vuol dire solo che non viola nessun vincolo per costruzione.

---

## 2. Schede delle sopravvissute

Regole comuni a tutte:
- Solo sessione RTH 09:30–16:00 ET. **Uscita forzata alle 15:55 ET** (flat EOD, prima del cut-off Lucid delle 16:45).
- Stop e target sono ordini **bracket inviati all'ingresso**.
- Massimo 1 trade per strategia al giorno, salvo dove indicato.
- Si escludono i **giorni di roll** del continuous (il back-adjust crea gap artificiali tra close e open) e il primo giorno dopo il roll.
- Le distanze sono in **punti o in multipli di ATR(14) giornaliero**, con tetto e pavimento. Mai percentuali.

### #1 – Fade del gap piccolo (MNQ, alternativa MES)

- **Ipotesi:** i gap piccoli tra il close RTH di ieri e l'open RTH di oggi tendono a richiudersi nella sessione.
- **Perché dovrebbe funzionare (chi perde):** chi reagisce alle notizie overnight a liquidità bassa sposta il prezzo. All'open i market maker e i ribilanciatori riportano il prezzo verso il valore RTH. Perde chi insegue il gap all'apertura.
- **Regole:**
  - `Gap = Open(09:30) − Close RTH(t−1)`, in punti.
  - Condizione: `0,10×ATR14d ≤ |Gap| ≤ 0,35×ATR14d`, con |Gap| ≥ 15 pt NQ (pavimento, così il target supera i costi) e ≤ 60 pt NQ (tetto).
  - Ingresso alla chiusura della prima barra 5m (09:35) solo se quella barra **non** ha già chiuso il gap.
  - Direzione contraria al gap. Target = Close(t−1). Stop fisso 55 pt MNQ (22 pt MES). Uscita 15:55 se nessuno dei due è stato toccato. Lunedì escluso (variante da testare).
- **Rischio per trade:** 55 pt × $2 = **$110/micro MNQ**; MES 22 pt × $5 = $110.
- **Perché rispetta il profilo:** con target medio intorno a 0,5–0,9R e stop a 55 pt, il WR deve essere ≥60% perché il PF superi 1,3. n/anno ≈ 80–120 (circa un terzo-metà dei giorni ha un gap in banda: **stima**, il dato preciso non ce l'ho). Il target è il close precedente: nessuna logica percentuale.
- **Cosa la falsifica:**
  - WR first-touch (target prima dello stop) < 58% su 2020–2024;
  - netto/trade < $70 per mini;
  - più del 50% del profitto concentrato nel 2020 o nel 2022 (anni ad alta volatilità).
- **Fonte:** tradingstats.net, 2.791 giorni NQ (2015–2025). Riporta fill entro il close nel 60,3% dei casi, MAE mediana 44 pt, P75 107 pt, P90 203 pt, e MAE mediana ≈ 28 pt per i gap minimi. Sono **statistiche descrittive, non un trade test**: misurano il fill "prima o poi", non "target prima dello stop". Il **93,1%** citato per "gap minimo + conferma della prima candela 15m" è un tasso di fill, **non un WR**.
- **Cosa non so:**
  - WR first-touch con stop a 55 pt: con MAE P75 a 107 pt su tutti i gap, una parte dei fill verrà stoppata prima;
  - la distribuzione delle dimensioni dei gap in ATR su 2020–2024;
  - se la definizione di gap della fonte (RTH-RTH) coincide con il mio session setting in MultiCharts.

### #2 – Fade dell'estremo di sessione poco profondo (MES/MNQ)

- **Ipotesi:** un nuovo massimo o minimo di sessione poco lontano dall'open (in ATR) tende a ritracciare. Gli estremi lontani sono trend da non toccare.
- **Chi perde:** chi compra il nuovo massimo in giornate di rotazione (breakout trader intraday).
- **Regole:**
  - `Dist = (Prezzo − Open RTH)/ATR14d`.
  - Short quando una barra 5m segna un nuovo massimo RTH con `0,25 ≤ Dist ≤ 0,50`, nella finestra 10:00–14:30, e la barra **chiude** sotto il massimo della barra precedente. Long simmetrico sui minimi (la fonte dice che i minimi ritracciano più spesso: variante "solo long" da testare).
  - Target = Open RTH, con tetto a 0,9R e pavimento a 8 pt MES (sotto il pavimento si salta il trade).
  - Stop fisso 22 pt MES / 55 pt MNQ. Al massimo 1 trade al giorno.
  - Filtro: niente trade se `Dist > 0,5` è già stata toccata nel giorno (giornata trend).
- **Rischio:** **$110/micro.**
- **Perché rispetta il profilo:** il target sull'open dà R:R strutturalmente ≤1. Le occasioni sono frequenti, quindi ≥200 trade in 5 anni sono plausibili.
- **Cosa la falsifica:** WR first-touch < 58%; PF < 1,35; edge che sparisce nel 2022.
- **Fonte:** tradingstats.net, 1m NQ/ES/YM/RTY 2019–2026 (≈14.300 estremi per mercato). Gli estremi poco profondi ritracciano a metà circa l'85% delle volte, con un crollo tra 0,3 e 1,0 ATR verso ~20%. La fonte stessa **avverte che il tasso di ritracciamento eventuale non è un WR** e che uno stop stretto ne perde una parte. Descrittivo, non testato. In più l'estensione è misurata dall'open delle 18:00 ET (sessione Globex), non dall'open RTH: **nella mia regola cambia il riferimento**, quindi i numeri della fonte non si trasferiscono direttamente.
- **Cosa non so:** WR con stop fisso a 22 pt; quanti segnali al giorno superano il pavimento del target.

### #3 – Ritorno all'open settimanale (MNQ/MES, intraday Mar–Ven)

- **Ipotesi:** il prezzo torna spesso all'open RTH del lunedì entro la settimana, tanto più quanto è vicino.
- **Chi perde:** chi estrapola il movimento del lunedì. Sui livelli di inizio settimana agiscono i ribilanciamenti.
- **Regole:**
  - `WO = Open RTH del lunedì`.
  - Tra martedì e venerdì, all'open RTH: se `0,20×ATR14d ≤ |Open − WO| ≤ 0,60×ATR14d` e la distanza è ≥ 30 pt NQ (gate costi), entrare verso WO alla chiusura della barra 15m delle 09:45.
  - Target = WO. Stop 55 pt MNQ. Uscita 15:55. Una volta toccato WO, la strategia è chiusa per la settimana.
- **Rischio:** **$110/micro.**
- **Perché rispetta il profilo:** WR atteso alto e target sotto 1R. n/anno 45–70: **al limite** dei 200 trade in 5 anni (rischio di fallire il gate n). Rispetta comunque i ≥40 trade/anno di attività.
- **Cosa la falsifica:** n < 200 su 2020–2024; netto < $70; WR intraday < 60%.
- **Fonte:** tradingstats.net, 565 settimane NQ. Tocco di WO tra martedì e venerdì nel 69,7% delle settimane, 92,9% se il martedì apre entro lo 0,25%, 48% se lontano. Descrittivo. Misura il tocco **su 4 giorni**, mentre io devo essere flat ogni sera, quindi il WR intraday sarà **nettamente più basso**. Le soglie della fonte sono in %: le ho convertite in ATR, quindi i loro numeri non si applicano 1:1.
- **Cosa non so:** probabilità di tocco **nella stessa sessione**. È il dato cruciale e non l'ho trovato.

### #4 – Sweep fallito di PDH/PDL (MES)

- **Ipotesi:** una breve violazione del massimo o minimo di ieri, seguita da un rientro, segnala stop eseguiti senza follow-through.
- **Chi perde:** i breakout trader e chi viene stoppato sul livello ovvio.
- **Regole:**
  - Nella finestra 09:45–14:30, una barra 5m supera il PDH (massimo RTH di ieri) di almeno 2 pt MES e poi una barra 5m, entro al massimo 3 barre, **chiude** sotto il PDH. Short alla chiusura di quella barra.
  - Stop fisso 22 pt. Target fisso 18 pt (R:R 0,82). Simmetrico sul PDL.
  - Al massimo 1 trade per lato al giorno.
- **Rischio:** **$110/micro.**
- **Perché rispetta il profilo:** target fisso con R:R 0,82 per costruzione. WR pari al 55% darebbe PF ≈ 1,0: **servono ≥62%**.
- **Cosa la falsifica:** WR < 60% o PF < 1,35.
- **Fonte:** blog Medium (Steady Turtle), aneddoti e WR dichiarati senza dati. **Affermato, non testato.**
- **Cosa non so:** tutto il profilo statistico.

### #5 – Fade della banda VWAP ±2σ con target limitato (MES)

- **Ipotesi:** gli eccessi oltre la banda 2σ del VWAP RTH rientrano parzialmente.
- **Chi perde:** chi insegue gli eccessi intraday. Gli algoritmi di esecuzione ancorati al VWAP riportano il prezzo verso la media.
- **Regole:**
  - VWAP RTH con bande σ (calcolo intrabar, solo prezzo e volume: nessun order flow).
  - Nella finestra 10:00–15:00: chiusura 5m oltre +2σ seguita da una chiusura 5m di nuovo dentro +2σ → short.
  - Target = min(+1σ, 18 pt). Stop 22 pt fissi.
  - Filtro trend: niente trade se la larghezza della banda 1σ alle 10:30 è > 0,35×ATR14d.
- **Rischio:** **$110/micro.**
- **Perché rispetta il profilo:** il target limitato tiene R:R ≤ 0,82.
- **Cosa la falsifica:** WR < 60%; edge concentrato in un solo anno.
- **Fonte:** futureshive e proptradingvibes. Dichiarano un "75–80%" di rientro a 2–3σ senza metodo né dati. **Affermato, non testato.** Da trattare come marketing.
- **Cosa non so:** WR reale; sensibilità al filtro trend.

### #6 – Fade della prima uscita dal range overnight (MGC), marginale

- **Regole:**
  - Range overnight = massimo/minimo 18:00–08:20 ET.
  - Nella finestra 08:20–12:00, alla prima chiusura 5m fuori dal range seguita da una chiusura dentro, entrare in direzione opposta.
  - Stop 12 pt MGC ($120). Target = min(metà del range, 10 pt).
  - Pavimento: range overnight ≥ 8 pt, altrimenti nessun trade.
- **Problemi:**
  - gate costi: serve netto ≥ $140 per GC, cioè lordo ≥ 1,65 pt/trade su R = 12 pt → E ≥ 0,14R → PF ≈ 1,4 minimo;
  - **nessuna fonte trovata**, è solo un'ipotesi;
  - i dati macro delle 08:30 ET (CPI, NFP) cadono dentro la finestra: escludere 08:25–08:40 non richiede giudizio umano, basta un calendario statico.

**Il dato che manca:** qualsiasi statistica sul re-entry nel range overnight di GC.

### #7 – Fade del falso breakout dell'OR a 30 min (MES), marginale

- **Regole:**
  - OR = 09:30–10:00.
  - Rottura del massimo dell'OR seguita, entro 30 minuti, da una chiusura 5m dentro l'OR → short.
  - Stop 22 pt. Target = metà dell'OR, con tetto a 18 pt.
- **Problemi:**
  - è **adiacente alla famiglia breakout** già esclusa su NQ, quindi la propongo **solo su MES**;
  - l'unica evidenza è indiretta: uno studio di falsificazione su MNQ (2021–2025, 14 famiglie di segnali OHLCV, ORB incluso) non trova edge. Ma "il breakout non funziona" non implica "il fade funziona".

---

## 3. Scartate (motivo in una riga)

- **Intraday momentum "Noise Area" (Zarattini-Aziz-Barbon, SPY):** trend-following con trailing stop e upside illimitato. Profilo a basso WR e alto R:R, escluso per costruzione. Il trailing VWAP rende anche lo stop variabile.
- **Varianti ottimizzate della Noise Area (Maróy 2025):** stessa famiglia, in più c'è overfitting dichiarato (ottimizzazione di tutti i parametri).
- **Last half-hour momentum (Gao-Han-Li-Zhou, JFE 2018):** testata seriamente, ma l'R² è ~1,6%: il movimento medio dell'ultima mezz'ora su ES quasi certamente non arriva a netto ≥ $90 per mini. Un lavoro successivo riporta l'effetto attenuato nel 2007–2018. WR atteso ~52–54%: fallisce WR e costi.
- **Breakout direzionale/ORB su @NQ:** escluso per vincolo (già morto 3 volte).
- **VWAP pullback in trend con target 1,5–2R e stop sul swing:** R:R fuori profilo e stop non dichiarato a priori.
- **RSI(2)/Connors e mean reversion multi-day:** richiedono di tenere la posizione overnight.
- **Strategie basate su gamma/0DTE, footprint/CVD, DOM:** dati vietati (opzioni, order flow).
- **Weekly open con tenuta fino a venerdì:** viola il flat EOD. Sopravvive solo la versione intraday (#3).
- **Classificatore ML di regime (VVG su MNQ):** regole non semplici da tracciare, rischio di data-mining. Al massimo può diventare un filtro dopo che una base ha superato i gate.

---

## 4. Note a parte (non modificano i criteri)

1. **Tensione tra il gate di drawdown e il tempo per passare l'eval.** Con R = $110/micro e PF 1,4, il netto atteso è ~$15 per trade per micro. Con 1 micro servono ~200 trade per fare $3.000 (cioè anni). Con 4 micro servono ~50 trade, ma DD 95° ≈ 15R × $440 = $6.600, più del MLL di $2.000. Approssimazione da gambler's ruin con drift (la mia, ignorando il trailing): P(pass) ≈ 99% a 1 micro, ≈ 86% a 4 micro. Il trailing EOD la abbassa ancora, di quanto **non** l'ho calcolato. Il gate per-micro garantisce la sopravvivenza della strategia, non il passaggio dell'eval in tempi utili: la size va decisa con un Monte Carlo specifico sull'eval.
2. **Il gate PF ≥ 1,2 è di fatto non vincolante.** Il vincolo combinato DD + costi richiede ~1,35–1,4 (§0). Lo segnalo, non lo riscrivo.
3. **Il rischio di Monte Carlo con riordinamento è ottimistico per il mean reversion:** le perdite arrivano a grappoli nelle giornate trend, e il riordinamento i.i.d. rompe proprio quella dipendenza. Suggerisco di affiancare un block bootstrap (per settimana) al Monte Carlo richiesto.
4. **Consistency 50%:** con R:R < 1 e 1 trade al giorno, un singolo giorno vale al massimo ~+0,9R × size, quindi la regola si rispetta in modo naturale.
