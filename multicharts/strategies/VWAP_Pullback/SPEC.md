# SPEC — VWAP Pullback NQ (Stage 0)

**Ipotesi**: dopo che NQ ha rotto il range 08:30–09:00 CT (bias della sessione), il
primo ritorno sul VWAP di sessione e la ripresa nella direzione del bias è un ingresso
a prezzo migliore del breakout, con stop stretto e target al pivot precedente.
**Perché**: il 90%+ del flusso istituzionale è eseguito da algo benchmarked al VWAP;
il VWAP è la zona dove il flusso passivo si attiva e il prezzo reagisce. Chi perde: i
chaser che comprano il breakout e i fader del primo pullback. Nel corso: avg ~$80, PF
1.2, WR 58% (NQ 1 min dal 2021); variante con gate ADX (Agnello): WR 82%, avg $300 OOS
— **non verificata**, il codice ADX non è nel materiale, va ricostruita.
Ruolo nel basket: la componente "mean reverting" (compra il ritorno al VWAP) con
correlazione ~0 rispetto a ORB/VaultBreak.

| | |
|---|---|
| Famiglia | mean reverting a livello micro, continuation a livello di sessione |
| Strumento · TF · sessione | @NQ · **1 min** · Globex 24h, chart CT, MaxBarsBack ≥ 42 |
| Bias | close fuori dal range 08:30–09:00 CT (latched) |
| Entry | retest del VWAP di sessione (touch, o close‑through + reclaim) → a mercato sulla chiusura del reclaim, nella direzione del bias, 09:00–14:00 CT |
| Stop | pivot swing (StopSwingLen 20) o estremo del pullback (StopMode 2) |
| Target | ultimo pivot confermato (TargetSwingLen 5) |
| Time exit | **flat 14:55 CT obbligatorio** (`UseEODFlat true` — l'originale tiene overnight: non ammesso per la prop) |
| Trade/giorno | 1 |
| Profilo prop | da verificare: R:R variabile (pivot); se < 55% WR → Stage 4 con TP fisso 0.5–1R |

**IS**: 2021‑01‑01 → 2024‑12‑31 (dati 1 min) · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: gate ADX(14) > 20/25 sul 5 min; StopMode 1 vs 2;
MinRR 1; TP fisso in R al posto del pivot; long only.
**Note codice**: template `13. VWAP Pullback NQ Margin Vol 1min TF.txt` — usare
`UseVolSizing false`, `PositionSize 1`, `UseEODFlat true`. Volume da trade data.
**Kill**: gate pipeline; se con EOD flat l'avg trade scende sotto $70, non sopravvive ai costi.

---

# Pre‑registrazioni prima dello Stage 1 (13/10/2026)

## 1. La base resta la v1 ripulita. Il gate ADX resta Stage 4.

Il materiale nuovo del protocollo (13/10) contiene **`VWAP Pullback + ADX gate.txt`, la v4**
del Bridge: v3 aggiunge il gate ADX, v4 il risk sizing. Chiude il buco annotato qui sopra
(«*il codice ADX non è nel materiale, va ricostruita*»).

**Non diventa la base.** Questa spec pre‑registra il gate ADX come **variante Stage 4**, e
Stage 4 viene dopo Stage 3. La v4 lo attiva di default nel suo profilo «C.S.», ma quella è
una scelta dell'autore, non la nostra pre‑registrazione.

Quindi: **Stage 1 e Stage 2 girano su `VWAP_Pullback.txt`**, la v1 ripulita già in repo
(EOD flat attivo, 1 contratto fisso, filtri off). Dalla v4 si prende **solo il codice del
gate ADX**, e solo quando si arriverà allo Stage 4.

Questo è l'opposto di quello che è stato fatto su Gold Asian Range, dove una
pre‑registrazione è stata scavalcata su 78 trade e quattro mesi e si è rivelata giusta.
Vale la regola scritta nel cimitero: **una pre‑registrazione non si rivede su un campione
più piccolo di quello su cui verrà giudicata.**

## 2. Il rischio per trade non è dichiarato: va misurato prima del Gate 2

Lo stop è un **pivot swing** (`StopMode 1`, `StopSwingLen 20`), quindi di **ampiezza
variabile**: a differenza di First5 (`StopPts` esplicito) il rischio per trade non si
sceglie, si scopre. È il difetto che ha ucciso ORB, VaultBreak e First5, trovato al
Gate 2/3 invece che prima.

Il log esistente lo rende misurabile senza toccare il codice: stampa `close=` e `stop=` a
ogni ingresso, quindi `stopDist = |close − stop|`. Con `MinRR 0` e `MaxStopPoints 0` nessun
setup viene scartato, quindi **il campione dei trade è il campione dei setup**: la misura
non è distorta per selezione.

Soglie già note, contro cui si legge: Gate 2 vuole **trade peggiore ÷ 10 ≤ $500**, Gate 3
vuole **DD 95° pct ÷ 10 ≤ $2.000**. Su @NQ 1 punto = $20, quindi su MNQ = $2: **uno stop di
250 punti vale $500 per micro**, ed è il tetto oltre il quale non si passa.

## 3. La misura va fatta sull'IS, non su un campione recente

Lezione diretta dalla morte di Gold: lo Stage 1 girava su quattro mesi del 2026, un regime
in cui il range asiatico più largo di quattro mesi superava il più largo dei cinque anni
precedenti. I numeri di rischio letti là non valevano per il 2020‑2024.

Quindi **fra lo Stage 1 e lo Stage 2 si inserisce un run di sola misura**: stesso codice,
`ShowLog 1`, chart sull'**IS intero 2021‑2024**, e si legge la distribuzione di `stopDist`.
Se il p90 sta sopra i 250 punti, non si spende lo Stage 2.

Non è una modifica al protocollo: il Gate 1 chiede solo «meccanica corretta al 100%» e non
ha mai preteso di validare l'unità di rischio. È un controllo in più prima di investire run,
non un gate nuovo.

## 4. Due offset da uno sbaglio già fatto una volta

Le barre MC sono timbrate a **fine periodo** — verificato su Gold, dove la barra `2400`
allargava la finestra del range di un quarto d'ora senza che si vedesse nel report.

A 1 minuto, `inORB = Time >= 830 and Time < 900` prende le barre `0830…0859` = **30 barre**,
che coprono **08:29 → 08:59**. L'opening range è quindi spostato **un minuto indietro**
rispetto al 08:30–09:00 della spec. Su una finestra di 30 minuti è il 3,3%: trascurabile,
ma **scritto adesso** per non scoprirlo dopo e non poterlo usare come spiegazione comoda.

Lo stesso vale per `EntryStartTime 900`: la prima barra ammessa è quella timbrata `0900`,
che copre 08:59–09:00, cioè l'ultimo minuto dell'opening range. Da verificare nel log che
nessun ingresso cada lì.

## 5. Rischio dati, dichiarato in anticipo

L'IS è **@NQ a 1 minuto dal 2021**: circa 1,4 milioni di barre. Due cose possono rompersi e
non sono difetti della strategia: la **profondità storica** dei dati a 1 minuto, e il
**tempo di esecuzione** del backtest con Bar Magnifier. Se i dati non arrivano al 2021,
l'IS si accorcia e va annotato prima di leggere i risultati, non dopo.

---

# Pre‑registrazione 6 — come si fissa `MinStopPoints` (14/10/2026, prima della misura)

Lo Stage 1 ha trovato che lo stop a pivot swing non ha pavimento: 4 trade su 78 con lo stop
a ≤ 1 punto, uno a **un tick**, tutti e quattro in perdita. Serve un `MinStopPoints`, ma a
differenza del tetto **non esiste una soglia di gate da cui derivarlo**.

Il tetto è già fissato e non si discute: Gate 2 vuole trade peggiore ÷10 ≤ $500, su MNQ
1 punto = $2, quindi **`MaxStopPoints 250`**. Derivato dal gate, non dai dati.

Per il pavimento si misura il **rumore** con `VWAP_Noise_Study.txt`, e si applica questa
regola, scritta adesso:

> **`MinStopPoints` = la mediana di `r15`**, l'escursione a quindici minuti di @NQ nella
> finestra di ingressi, arrotondata al punto intero.

**Perché `r15` e non un'altra colonna.** Un trade di questa strategia entra fra le 09:11 e
le 13:58 e dura in media ore: un target mediano di 74 punti non si raggiunge in pochi minuti.
Uno stop più stretto dell'escursione tipica di un quarto d'ora verrà quindi colpito dal
rumore nei primi minuti, prima che la tesi del trade abbia modo di realizzarsi o di essere
smentita. `r5` sarebbe troppo permissivo (quindici secondi di rumore non sono un test della
tesi), `r30` troppo severo (taglierebbe stop legittimi). `atr14` serve come controprova: se
la mediana di `r15` e l'ATR a 1 minuto raccontano scale molto diverse, la misura va riletta
prima di usarla.

**Cosa NON decide questa regola.** Non è un'ottimizzazione: non si prova `MinStopPoints` a
più valori per vedere quale rende. Il numero esce dalla misura del rumore, che è una
proprietà dello strumento e non dei risultati della strategia.

**Il seguito resta vincolato.** `MinStopPoints` e `MaxStopPoints` sono **filtri**: tolgono
trade. Quando si applicano, devono passare il **test split‑sample** sull'IS come ogni altro
filtro. Se non lo passano, non entrano, qualunque cosa dica il netto.

**Resta off‑limits** il tetto a 100 punti che nei dati dello Stage 1 rende il campione
positivo (n=33, avg +$146, PF 1,46). Non è pre‑registrato come valore e sarebbe scelto
guardando il risultato. Tetti diversi da 250 si testano allo Stage 4, dopo lo Stage 3, con il
range dichiarato prima.

---

# Stage 2 — IS 2021‑2024: **Gate 2 fallito da entrambe le versioni**

Chart @NQ 1 min, 2021‑01‑04 → 2024‑12‑31, 1 contratto, $7,50/contratto, Bar Magnifier off.
Report in `reports/VWAP_S2_*.xlsx`.

| criterio | soglia | BASE | FILTRO (`MinStop 60`, `MaxStop 250`) |
|---|---|---|---|
| n | ≥ 200 | 764 ✅ | 605 ✅ |
| **avg trade** | ≥ $70 | **$9** ❌ | **$33** ❌ |
| **Profit Factor** | ≥ 1,2 | **1,02** ❌ | **1,08** ❌ |
| WR | ≥ 55% | 56,3% ✅ | 72,9% ✅ |
| avg win / avg loss | 0,5–1 | 0,79 ✅ | **0,39** ❌ |
| **DD ÷ 10** | ≤ $1.000 | **$2.380** ❌ | **$1.618** ❌ |
| trade peggiore ÷ 10 | ≤ $500 | $444 ✅ | $444 ✅ |
| nessun anno > 50% | | **2022 negativo** ❌ | **2023 = 67%** ❌ |

## Il risultato vero: entrambe stanno sul pareggio

| | R:R | WR di pareggio | WR osservato | margine | t |
|---|---|---|---|---|---|
| BASE | 0,79 | **55,9%** | 56,3% | **+0,4 punti** | 0,23 |
| FILTRO | 0,39 | **71,8%** | 72,9% | **+1,1 punti** | 0,69 |

PF 1,02 e 1,08 non sono sfortuna: sono l'aritmetica di quei margini. Su 764 e 605 trade il
t resta sotto 1 — **l'edge non è distinguibile da zero.**

## Il filtro funziona nelle due metà, e non basta

| | BASE | FILTRO |
|---|---|---|
| IS intero | avg $9 · PF 1,02 | avg $33 · PF 1,08 |
| 1ª metà 2021‑22 | avg **−$29** · PF 0,93 | avg **+$19** · PF 1,04 |
| 2ª metà 2023‑24 | *non eseguito* | avg $46 · PF 1,11 |

Migliora in entrambe le finestre confrontabili. Il sesto run **non è stato chiesto**: il
verdetto di Gate 2 si giudica sull'IS intero, che c'è, e falliscono entrambe le versioni.
Lo split‑sample avrebbe deciso solo *quale* delle due fosse la candidata.

## Due questioni tecniche chiuse

- **Bar Magnifier off, e non incide.** 0 trade su 764 esce nella stessa barra d'ingresso.
  Con stop ≥ 60 punti e target a 0,39× lo span del bracket è ~83 punti contro un ATR a 1
  minuto di 16: una barra che li contenga entrambi è ~5 volte l'ATR. Trascurabile.
- **La predizione registrata il 14/10 era giusta**, e in anticipo: avevo scritto che avrebbe
  fallito sul drawdown. Fallisce al **Gate 2** ($1.618/micro), non al Gate 3.

## Perché, strutturalmente

La finestra ammissibile dello stop, ricalcolata al **suo** n reale (600 trade su 4 anni),
con i gate sul drawdown e il pavimento dei costi:

| profilo | R max dal DD | R min dai costi | finestra |
|---|---|---|---|
| **WR 56% · R:R 0,80** *(il profilo osservato)* | 22 pt | 531 pt | **VUOTA** |
| WR 60% · R:R 0,80 | 37 pt | 53 pt | **VUOTA** |
| WR 60% · R:R 0,90 | 45 pt | 30 pt | 30–45 pt ($61–90/micro) |
| WR 62% · R:R 1,00 | 56 pt | 18 pt | 18–56 pt ($35–111/micro) |
| WR 65% · R:R 1,00 | 71 pt | 14 pt | 14–71 pt ($28–143/micro) |

**Al profilo osservato la finestra è vuota di un fattore 24.** Si apre solo con
**R:R ≥ 0,90 e WR ≥ 60%**, e richiede uno stop fra 30 e 56 punti. Lo StopMode 1 misurato ne
ha **109,50** (base) e **121** (filtrato).

Tre condizioni, tutte e tre mancate. Non è un gate che inciampa: è la geometria dello stop.

---

# Pre‑registrazione 7 — la misura `StopMode 2`, e la regola che la giudica (14/10/2026)

Scritta **prima** del run.

`StopMode 2` mette lo stop all'**estremo del pullback** invece che al pivot swing a 20 barre,
lasciando il target dov'è. Quindi muove **due** cose nella direzione giusta insieme: lo stop
si accorcia e il R:R sale. È l'unica variante pre‑registrata che tocchi la geometria, e il
difetto misurato è geometrico.

Il prezzo: uno stop più vicino viene colpito più spesso, quindi il WR scende. La domanda è
se scenda sotto 60% prima che il R:R arrivi a 0,90.

## Il run

| | |
|---|---|
| Chart | @NQ 1 min, ~100 giorni (lo stesso dello Stage 1) |
| `StopMode` | **2** |
| **`MinStopPoints` / `MaxStopPoints`** | **0 / 0** — i filtri vanno **spenti**: misuriamo la distribuzione grezza, filtrarla significherebbe misurare il filtro |
| `ShowLog` | **1** |
| Resto | default · 1 contratto · $7,50/contratto |

Serve **report + log**: il log dà `stopDist` e R:R, il report dà il WR.

## La regola di decisione

| # | Condizione | Soglia | Affidabilità su ~78 trade |
|---|---|---|---|
| 1 | mediana di `stopDist` | **fra 30 e 56 punti** | **alta** — è geometria, non esito |
| 2 | mediana di R:R | **≥ 0,90** | **alta** — idem |
| 3 | WR | ≥ 60% | **bassa** — su 78 trade l'errore standard è ~5,5 punti |

**Le condizioni 1 e 2 decidono.** Sono proprietà della geometria di stop e target, misurate
bene anche su 78 trade, e le soglie vengono dalla tabella della finestra qui sopra — cioè dai
gate, non dai risultati.

**Se 1 o 2 mancano → cimitero**, senza altri run. La finestra sarebbe vuota per costruzione e
nessun filtro la riempie.

**Se 1 e 2 passano**, la condizione 3 non è decisiva su 78 trade: giustifica un run Stage 4
sull'IS per misurare il WR sul campione vero. Non è un via libera, è il permesso di spendere
un altro run.

---

# `StopMode 2`: la regola ha sparato — **cimitero, causa A** (14/10/2026)

Run di misura come pre-registrato: ~100 giorni, `StopMode 2`, filtri a 0, `ShowLog 1`.
Report `reports/VWAP_S4_stopmode2_100gg.xlsx`, log `VWAP_S4_stopmode2_log.txt`.

## La regola, applicata

| # | Condizione | Soglia | Misurato | |
|---|---|---|---|---|
| **1** | mediana `stopDist` | **30–56 pt** | **20,75 pt** | ❌ |
| 2 | mediana R:R | ≥ 0,90 | **4,18** | ✅ |
| 3 | WR | ≥ 60% | **26,6%** | ❌ |

La condizione 1 era una delle due decisive. **Il verdetto pre-registrato è il cimitero, senza
altri run.**

## I tre assetti tracciano una curva, e nessuno tocca la regione ammissibile

| assetto | stop mediano | WR | R:R | WR di pareggio | esito |
|---|---|---|---|---|---|
| `StopMode 1` base | **109,50 pt** | 56,3% | 0,79 | 55,9% | pareggio, stop **troppo largo** |
| `StopMode 1` + filtri 60/250 | **121 pt** | 72,9% | 0,39 | 71,8% | pareggio, R:R **sotto banda** |
| `StopMode 2` | **20,75 pt** | **26,6%** | 2,09 | 32,4% | **in perdita**, profilo **trend** |

Lo `StopMode 2` non ha solo accorciato lo stop: ha **capovolto il profilo**. WR 26,6% con
R:R 2,09 è esattamente la famiglia trend following che il profilo prop esclude per
costruzione — e perde, perché 26,6% sta sotto il pareggio di 32,4%.

Le uscite lo dicono senza ambiguità: **57 stop su 79 (72%)** contro 21 target.

## Perché era prevedibile dalla misura del rumore

| | |
|---|---|
| `r15` mediano su @NQ 1 min (misurato il 14/10) | **60,00 pt** |
| stop mediano `StopMode 2` | **20,75 pt** = **0,35× r15** |
| stop sotto il rumore a 15 minuti | **68 / 79 = 86%** |
| stop sotto il rumore a 5 minuti | 55 / 79 = 70% |
| stop sotto l'ATR a 1 minuto | 33 / 79 = 42% |

Il 42% dei trade ha lo stop **dentro una singola barra da un minuto**. Non è uno stop, è
rumore — ed è lo stesso difetto per cui era stato introdotto `MinStopPoints`, qui in forma
sistematica invece che su quattro trade.

## Il colpo di grazia aritmetico: la finestra e la frequenza non coesistono

Solo **15 trade su 79 (19%)** hanno lo stop dentro la finestra 30–56 punti. Filtrare lo
`StopMode 2` alla finestra darebbe, sui 764 trade base di quattro anni, circa **145 trade**.

**Soglia di Gate 2: n ≥ 200.** Non esiste un assetto in cui lo stop stia nella finestra **e**
la frequenza basti. Non è una questione di parametri: è l'intersezione di due vincoli, e è
vuota.

## Lo split-sample, completato per il verbale

| | BASE | FILTRO |
|---|---|---|
| IS intero 2021‑24 | avg $9 · PF 1,02 · t 0,23 | avg $33 · PF 1,08 · t 0,69 |
| 1ª metà 2021‑22 | avg **−$29** · PF 0,93 | avg +$19 · PF 1,04 |
| 2ª metà 2023‑24 | avg **+$46** · PF 1,12 · t 0,87 | avg +$46 · PF 1,11 · t 0,73 |

La base passa da **negativa** nella prima metà a positiva nella seconda. Il filtro migliora in
tutte e tre le finestre — era quindi un filtro legittimo — ma migliora qualcosa che non c'è:
nessun t raggiunge 1 in nessun assetto.

# ✉️ Chiusa — cimitero, causa di morte **A**

**Causa A: edge assente.** Su 1.369 trade dell'IS più 79 della misura, in tre assetti che
coprono l'intera geometria di stop e target, **nessun t arriva a 1**. L'intervallo di
confidenza dell'avg trade contiene lo zero ovunque.

Non è causa B: il problema non è che l'edge non entri nel conto. È che non si misura.

## La lezione che resta, e chiude una classe

**Uno stop messo dalla struttura di mercato non è un'unità di rischio che possiamo scegliere.**

`StopMode 1` (pivot swing a 20 barre) dà 109 punti. `StopMode 2` (estremo del pullback) ne dà
20,75. La finestra ammissibile sta fra 30 e 56. **I due modi sbagliano in direzioni opposte**,
e la dispersione interna di ciascuno (0,25 → 386 e 0,25 → 179) è tale che nessun filtro li
porta dentro senza distruggere la frequenza.

Questo vale per **qualunque** stop ancorato a swing, pivot o estremo di pullback: la sua
dimensione la decide il mercato, non la spec. L'anti-pattern 3 del prompt di ricerca
(«unità di rischio non dichiarata») era scritto per intuizione; adesso ha la dimostrazione
completa, su entrambi i modi.

**Conseguenza operativa**: una candidata futura con stop strutturale non passa lo Stage 0
senza che la distribuzione dello stop sia misurata **prima**, e confrontata con la finestra
ammissibile dello strumento.
