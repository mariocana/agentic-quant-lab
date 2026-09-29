# Pipeline PROP — strategie per passare l'eval e incassare i payout

Obiettivo unico di questa fase: **strategie che passano una eval prop e portano al
payout**. Non capitale proprio, non "trovare l'edge del secolo". Il resto aspetta.

Come una pipeline CI: ogni stage ha un **gate**. Se il gate fallisce, la strategia si
ferma lì (o torna allo stage 4 se il problema è correggibile senza toccare l'OOS).
Niente eccezioni "però l'equity è bella".

Profilo target (Lezione 10, Live 1–5): **win rate ≥ 55–60%, R:R 0.5–1**, trade frequenti,
DD per micro contratto piccolo rispetto al limite della prop. Sviluppo sempre su **NQ
(o contratto pieno) a 1 contratto**; la size in micro la decide il simulatore.

> ## ⛔ Apex è fuori — automazione vietata (verificato 30/09/2026)
>
> Dalla pagina *Prohibited Activities* di Apex: **«No Automation or Algorithm Usage
> allowed»** — i premi riconoscono trader umani, non sistemi che eseguono logiche
> preprogrammate. Non è una zona grigia. Tutte e sei le nostre strategie sono vietate lì,
> e collegare MultiCharts via Rithmic non aggirerebbe nulla: violeremmo il contratto dal
> primo trade.
>
> **Prop di riferimento da ridefinire su Lucid Trading**, che ha MultiCharts nella lista
> piattaforme ufficiale e non vieta l'automazione (proibisce micro scalping, hedging e
> HFT, quest'ultimo definito come ordini in secondi/millisecondi — noi facciamo 1–4 trade
> al giorno). **Servono ancora i numeri**: max drawdown, daily loss, profit target e tipo
> di trailing (EOD o intraday) del conto che useremo, più conferma scritta
> sull'automazione. Fino ad allora le soglie sotto restano quelle vecchie, **da ricalcolare**.

Regole prop di riferimento ~~(Apex 50k, EOD trailing)~~ **obsolete, da rifare su Lucid**:
target $3.000, max DD $2.500, daily loss $1.000, 21 giorni, max 6 mini / 60 micro.
Nota: erano già superate di loro, perché Apex ha sostituito i prodotti il 1° marzo 2026 e
il 50k con quei parametri non è più acquistabile.

### Altre regole Apex che generalizzano

Valgono probabilmente anche altrove, quindi restano criteri di progetto:
- **niente trade senza stop** → conferma che `StopPts` è obbligatorio su NQ First5;
- **niente target minuscoli con stop enormi** (il loro esempio: 5 tick contro 150);
- **flat prima della chiusura**, obbligatorio → già nostro su tutte e sei;
- **niente hedging su strumenti uguali o correlati**, anche fra conti diversi → conferma e
  irrigidisce il gate 8: non si può tenere ORB long su NQ e una short su ES in parallelo.

---

## Stage 0 — Spec (prima di scrivere codice)
Scrivi in `mc/strategies/<nome>/SPEC.md`:
- ipotesi in una frase + **perché** dovrebbe funzionare (chi perde soldi contro di noi);
- famiglia (trend / mean reverting / evento), strumento, TF, sessione;
- entry, exit (TP/SL fissi o in R, time exit), un trade/giorno o max N;
- **date IS e OOS** (80/20) e criteri di kill, **decisi ora**.

- **worst day strutturale** in $: quanto può perdere la strategia nella sua giornata
  peggiore *per costruzione*, non nel backtest. Se la risposta è "dipende", mancano i
  guardrail (cap ingressi/giorno e cap perdite/giorno) e vanno aggiunti **ora**.

**Gate 0**: tutto scritto. Nessuna spec = nessun codice.

> **I guardrail si scelgono prima del backtest, dalle regole del conto — non dopo, dalla
> curva di equity.** La strategia si adatta al conto, mai il contrario. Un worst day noto
> in anticipo è ciò che rende una strategia deployabile su un trailing drawdown; un worst
> day scoperto nell'equity curve è solo una statistica. (Da DriftPullback, sez. 08.)

## Stage 1 — Codice e meccanica
Signal PowerLanguage, flag 0/1, 1 contratto, ~100 giorni di dati, `ShowLog`.
Controllo su chart + List of Trades: trade dove previsto, un trade/giorno, flat all'ora
prevista, SL/TP = quelli della spec, con 10 contratti P&L ×10, nessun trade nel weekend
non voluto (half‑day: annotare).

**Gate 1**: meccanica corretta al 100%. Report salvato in `reports/`.

## Stage 2 — Backtest IS (1 contratto, costi on)
Costi: $2.50/lato + 1 tick. Solo il periodo IS.

**Gate 2** (tutti):
| Metrica | Soglia |
|---|---|
| n. trade IS | ≥ 200 |
| avg trade netto | ≥ soglia strumento (NQ $70 → MNQ $7; GC $140) |
| profit factor | ≥ 1.2 |
| win rate | ≥ 55% (profilo prop) |
| R:R nominale | 0.5–1 |
| max DD 1 contratto ÷ 10 (micro) | ≤ 50% del DD prop (**soglia da ricalcolare su Lucid**; col vecchio riferimento Apex: ≤ $1.250) |
| peggior trade ÷ 10 | ≤ 50% daily loss (≤ $500) |
| tabella annuale | nessun anno > 50% del profitto; segno stabile 2021‑23 vs 2024+ |

## Stage 3 — Monte Carlo built‑in (IS)
Reshuffle 1000 sim, 100% trade; Distribution analysis.

**Gate 3**: mediana net profit > 0; < 10% simulazioni in perdita; DD 95° perc. ÷ 10
≤ DD prop ($2.500).

## Stage 4 — Miglioramenti (solo IS)
Base case = versione senza filtri. Ogni aggiunta deve avere una ragione e passare lo
**split‑sample** (due metà dell'IS, migliora l'avg trade in entrambe). Ottimizzazione
a due passi, ≤ 3 input, step larghi, fitness PF; si sceglie il cluster.
Per il profilo prop: testare TP 0.5R vs 1R, cutoff ingressi, `MaxRisk_USD` (salta i
giorni in cui 1 micro rischia troppo).

**Gate 4**: regole semplici e spiegabili; ≤ 3 input ottimizzati; rifare Gate 2 e 3.

### Stage 4b — Walk‑forward: come lo usiamo (diagnostico, opzionale, **solo IS**)

Il walk‑forward è nativo in MC (Optimize strategy → Walk Forward Optimization) e il corso
gli dedica l'Extra 3. **Da noi non è un gate e non è una modalità operativa.** È uno
strumento con un solo compito: dire se un parametro che abbiamo scelto allo Stage 4 è
**stabile fra i regimi** o se l'ottimo si sposta a ogni finestra.

**Come si lancia** (parametri fissati, non negoziabili dopo):
- finestre **rolling** IS 252 sessioni / OOS 63 (anchored solo se il regime è stabile);
- **interamente dentro il nostro IS** (2020‑01‑01 → 2024‑12‑31 ≈ 16 finestre). L'OOS della
  pipeline non si tocca: vale la regola dello Stage 5, una volta sola;
- fitness = **profit factor**, non net profit (è comparabile fra finestre di lunghezza e
  volatilità diverse);
- criteri di robustezza **scritti prima di premere Start**: avg OOS net profit > 0 · avg
  OOS PF > 1.1 · ≥ 60% finestre OOS positive · nessuna finestra > 50% del profitto ·
  ≥ 30 trade per finestra · **walk‑forward efficiency ≥ 60%** (sotto 50% = fit sul rumore).

**Come si legge il risultato** — e qui sta la differenza rispetto al corso:
- **passa** → il parametro è stabile: lo si congela al valore scelto e si va avanti. Non
  si adotta il "forecast", cioè la riottimizzazione ogni 63 giorni;
- **non passa** → il parametro è rumore: **si toglie l'input** e si torna al default del
  base case. Il walk‑forward serve a *scartare* un parametro, mai ad *adottare* un
  calendario di riottimizzazione.

**Perché non lo usiamo come modalità operativa** (il corso lo presenta anche così):
1. Il vantaggio vero del WFO è avere **pochi dati** — con tre anni dà più finestre OOS di
   uno split. Noi ne avremo 9 di storico a 1 minuto: il vantaggio non si applica.
2. Le nostre strategie hanno parametri **congelati per scelta** (DriftPullback, ORB dal
   Fabio Model). Una strategia che per restare viva va riottimizzata ogni trimestre
   fallisce comunque lo Stage 5.
3. È **più facile auto‑ingannarsi**, non meno: parole dell'autore, «basta pochissimo per
   cambiare i parametri e ottenere un pass quando la strategia non è abbastanza forte».
   Con lo split, un IS e un OOS entrambi buoni sono difficili da falsificare.
4. **Incompatibile col contesto prop.** Cambiare parametri ogni 63 giorni significa
   cambiarli dentro un'eval (21 giorni) o su un funded, sotto trailing drawdown. Le
   nostre regole di sospensione e ripresa (gate 8) sono definite sull'**equity**, non sui
   parametri; mescolare le due cose rende il pass rate simulato privo di significato.
5. **Costo operativo**: per dare i risultati WFO al simulatore prop bisogna esportare la
   lista trade di **ogni singola finestra OOS** una per una, con i suoi input, e
   ricucirle a mano in un unico file. Su 16 finestre × 6 strategie non regge.

**Quando invece il WFO sostituirebbe lo split**: strumento con storico corto (< 3 anni) o
dichiaratamente regime‑dipendente (es. crypto). Non è il caso di nessuna delle attuali.

## Stage 5 — Out‑of‑sample (una volta)
Parametri congelati sull'OOS.

**Gate 5**: avg trade, WR, PF nello stesso ordine di grandezza dell'IS (WR non sotto
50%); DD OOS ≤ DD IS × 1.5; equity con drift. Fail → **cimitero**, non si torna indietro.
Un walk‑forward che "passa" **non** riapre un fail dello Stage 5: non esiste un secondo
tentativo sull'OOS, in nessuna forma.

> **Notebook Colab da usare** (i link nei .txt delle lezioni sono superati; questi sono
> quelli aggiornati, citati nel PDF della Lezione 10 e usati nella Live 003):
> - Bootstrap EV / drawdown (Stage 6): `4. Validation…/2. Colab_Montecarlo.txt`
> - **Prop, singola strategia (Stage 7)**: https://colab.research.google.com/drive/1XyYJ4l-nZNPd8hgqdabHlHJPZXAwv4Up
> - **Prop, multi‑strategia (Stage 8)**: https://colab.research.google.com/drive/1lrWNv1uHRwQu3k9bfREOIJOmoHZ7Trza
>
> Le versioni aggiornate accettano direttamente l'export MC (niente CSV da ripulire),
> simulano il percorso **intraday** (stime più conservative) e calcolano il numero
> massimo di contratti "affidabile" (95° perc. della perdita per contratto vs DD prop):
> sopra quella soglia le stime diventano ottimistiche.

## Stage 6 — Bootstrap (Colab Monte Carlo, IS + OOS)
Export List of Trades → notebook. Risk per contract = SL medio in $.

**Gate 6**: EV > 0 in $ e in R; P(EV ≤ 0) < 5% IS, < 10% OOS; CI IS/OOS sovrapposti.
Salva percentili DD dopo 10/20/40 trade (yardstick live).

## Stage 7 — Simulatore prop, singola strategia (Colab prop single, OOS)
Regole della prop inserite; sweep sui micro; correlazione fra tentativi (i tentativi NON
sono indipendenti: in un regime ostile il pass rate cumulato scende — Live 004).

**Gate 7 — EVAL**: pass rate 1° tentativo ≥ 40%; entro 4 tentativi ≥ 85%; giorni medi
per passare ≤ 15; **eval scadute (expiry) < 5%**; DD medio < limite; size ottimale
≤ size "affidabile" (95° perc. perdita/contratto).
Riferimento: il basket del corso (VaultBreak + VWAP‑ADX + Overnight Bias) fa **52,5%**
al primo tentativo, 5 giorni medi, ~$191 di costo per conto funded.
Due obiettivi diversi, da non confondere (Live 005): massimizzare il **pass rate** non è
lo stesso che massimizzare i **conti funded per anno**. Un bracket aggressivo
(SL = daily loss, TP = 1.5× SL) abbassa il pass rate 52%→38% ma accorcia il ciclo e porta
da 26 a 35 funded/anno — conviene solo con un'aspettativa di payout alta per conto.
**La size compra la velocità, non le probabilità**: 1 mini e 2 mini hanno lo stesso pass
rate, ma 2 mini passano in 3 giorni invece di 6.
**Gate 7 — FUNDED**: qualification rate ≥ 50% alla size di sopravvivenza; expected
payout > costo del budget (≥ 4 × fee).

## Stage 8 — Basket (Colab prop multiple)
Tutte le strategie che hanno passato lo Stage 7 vanno nel simulatore multi‑strategia.

**Gate 8**: correlazione a coppie **vicina a 0, NON negativa** (Live 005: in ambiente prop
la correlazione negativa porta al rischio *hedging*, che è vietato); giorni attivi ≥ 90%;
pass rate del basket > migliore singola; qualification funded ≥ 70%; nessuna strategia in
drawdown oltre il **90° percentile** Monte Carlo al momento del deploy.
Size per strategia = output del simulatore (micro), cap totale ≤ 2 mini.

**Vincoli operativi multi‑account** (Live 005):
- **Mai posizioni opposte** su strumenti correlati, né nello stesso conto né fra conti
  diversi (long NQ su A + short ES su B = hedging → violazione). Soluzione: **una sola
  posizione aperta per volta** fra tutti i conti.
- **Non più conti che strategie**: nei test con 3 conti e trade distribuiti, il 17–25%
  delle eval **scadeva** senza passare né fallire. Una eval scaduta è peggio di una persa.
- Aprire una seconda eval mentre la prima è in corso **alza la correlazione fra tentativi**:
  accorcia i tempi ma abbassa il pass rate. È un trade‑off, non un pasto gratis.
- **Bench / ripresa**: si bencha una strategia quando il DD corrente supera il **90°
  percentile** della distribuzione Monte Carlo; si riprende solo a **nuovo massimo di
  equity** (non al recupero del 50% del DD). I fallimenti clusterizzano — e anche i
  successi: a una strategia sui massimi si può dare più peso.

## Stage 9 — Deploy
Paper ≥ 1 settimana; poi eval con size del simulatore, **budget dichiarato** (es. 3
tentativi), stessa strategia a ogni tentativo. VPS se > 1 strategia. Monitoraggio: DD vs
percentili (75° riduci, 95° stop), avg trade live vs backtest a 3 mesi. Piccole
randomizzazioni per non essere identici agli altri account.

---

## Stato

| Strategia | Famiglia | Stage | Note |
|---|---|---|---|
| ORB_Breakout (NQ 5m) | trend | **1 ✔ → 2 bloccato** | serve storico ≥ 5 anni (dati free = 4 mesi) |
| VaultBreak (NQ 5m) | trend | 0 ✔ → 1 | template del corso, codice pronto |
| VWAP Pullback (NQ 1m) | mean rev | 0 ✔ → 1 | template Agnello, codice pronto |
| Gold Asian Range (GC 15m) | trend, altro asset | 0 ✔ → 1 | winner Strategy of the Month |
| NQ First5 (NQ 5m) | momentum, **short** | 0 ✔ → 1 | template 18, non validato dall'autore |
| DriftPullback (NQ 5m + 15m) | momentum, long+short | 0 ✔ → 1 | Agnello v2.1, l'unica col profilo prop nativo |
| Evento macro (CPI/FOMC) | evento | — | dopo i primi tre |

**Blocco attuale**: la licenza MultiCharts (la trial non abilita dxFeed). Con dxFeed:
9 anni di barre a 1 min, 2 anni tick, live + DOM 10 livelli → copre storico e live.
Note dati: futures **non back‑adjusted** (irrilevante per strategie flat EOD; per Gold
Asian segnare i giorni di roll trimestrale nella lista trade); DOM storico assente →
il filtro delta si testa solo sugli ultimi 2 anni (tick).

---

## Avvertenza sulla mean reversion (Live 005)

Hanno testato **100+ strategie mean reversion intraday** con uscita a fine giornata:
**nessuna** risultava adatta all'ambiente prop, e non alzavano nemmeno il pass rate. La
mean reversion dà valore a livello di portafoglio, ma **multi‑day** — incompatibile col
trailing di Apex. Quello che aggiunge valore reale a un basket long‑only è invece una
strategia **long‑short o short‑only**.
Conseguenza: il nostro **VWAP Pullback** (unica "mean reverting" in lista) parte con un
sospetto a carico — se fallisce i gate non è sfortuna; e **NQ First5** copre il ruolo
davvero mancante, quello short.

## Candidati valutati e scartati

- **Gold/Silver Reversion** (template 17 del corso, GC vs SI, 5 min). Fade del movimento
  dell'oro relativo all'argento, z‑score su finestra mobile. Scartata: **nessun flat di
  fine giornata** (una posizione aperta blocca gli ingressi per settimane e porta rischio
  overnight/weekend, il peggio col trailing di Apex), pochissimi trade rispetto ai 21
  giorni di eval, e col default `HedgeRatio 5` il segnale è di fatto l'argento — nelle
  note dell'autore, sopra 2 «stai negoziando il movimento dell'argento con un contratto
  sull'oro», col rischio di un long oro travestito. L'autore la dà per non validata e i
  parametri stabili 2017‑2022 non si sono ripetuti nel 2023‑2026. Resta come materiale di
  studio in `mc/protocollo/6. Code Templates/1. Strategies/17. …`.

## Strumenti valutati — The Bridge (order flow L2/L3). Fuori pipeline

**Nessuna delle 6 strategie lo usa**: girano tutte su OHLC + volume e funzioni native
PowerLanguage. L'unico punto di contatto è il filtro delta opzionale dell'ORB
(`UpTicks − DownTicks`, `UseDeltaFilter` **0 = spento**), dove `UpTicks`/`DownTicks` sono
parole riservate **native di MC** alimentate dai dati tick del feed — non dal Bridge. Se
servisse, basta storico tick.

**Come funzionerebbe se un giorno ci servisse** (Extra 2, dettaglio completo nel digest §7):
MC non vede mai il book. Il Bridge calcola le feature nel suo processo («they cannot live
within MultiCharts») e 16 funzioni PowerLanguage fanno da interfaccia; lo storico entra in
MC come CSV importato da QuoteManager (ASCII mapping), e in live si danno al Bridge le
credenziali di un **feed proprio** (Databento, Rithmic, IQFeed, Continuum, Kanna) — il
Bridge non distribuisce dati, il feed L3 lo si paga a parte.

**Perché resta fuori**, in ordine di peso:
1. L'autore stesso, dopo due settimane di test: per il retail il valore dell'L3 «non è
   enorme», serve al più come **filtro** su una strategia che funziona già. Un filtro va
   validato con lo split‑sample come ogni altro → prima servono strategie che passino i
   gate **senza**.
2. La parte live è descritta **al condizionale e mai mostrata in funzione**: architettura
   dichiarata, non dimostrata.
3. **Simmetria storico/live** da verificare prima di scriverci sopra: ricerca sui dati
   campione del Bridge, live su un feed di un altro vendor → se la feature non è identica
   barra per barra, il backtest misura un'altra strategia.
4. **Entitlement**: DOM 10 livelli (L2) e MBO order‑by‑order (L3) sono due cose diverse e
   la seconda costa molto di più; da verificare anche cosa comprende l'entitlement
   Apex/Rithmic che useremmo in esecuzione.
5. Al momento è comunque **chiuso** (nessuna licenza acquistabile). Non blocca niente.

**Da rivalutare se riapre**, per un motivo che non c'entra con l'order flow: il suo
downloader dà **5+ anni di NQ a 1 minuto** (OHLCV + up/down volume) importabili in MC via
ASCII, buoni per backtestare qualsiasi strategia — cioè esattamente il blocco 1 di questa
pipeline.

---

## Ramo B — prop su CFD (FTMO & simili). Rimandato

Non ora, ma registrato per non ripensarci da capo:
- **FTMO non supporta MultiCharts**: si esegue su MT4/MT5, cTrader o DXtrade. Quindi non
  è un mirroring da MC ma un ramo separato su **MT5**, dove il lavoro MQL5 già fatto
  (`mql5/orb`, `ivb`, `range_breakout`, `Include/PropGuard.mqh`) torna utile.
- **Regole diverse → profilo diverso**: Apex ha il *trailing drawdown* (vincolo severo →
  WR alto, R:R basso); FTMO ha perdita massima **statica** dal saldo iniziale + limite
  giornaliero, più tollerante verso R:R alto e WR basso. Strategie scartate per l'eval
  Apex (es. Gold Asian variante A, WR 34% senza TP) potrebbero rientrare qui.
- Se e quando: servirà un simulatore prop adattato a quelle regole (il notebook del corso
  è scritto per il trailing di Apex) e nuove soglie nei gate 2, 3 e 7.
