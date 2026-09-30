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
> allowed»**. Non è una zona grigia. Tutte e sei le nostre strategie sono vietate lì, e
> collegare MultiCharts via Rithmic non aggirerebbe nulla.

## Prop di riferimento: **LucidFlex 50k** (verificato 30/09/2026)

Automazione **esplicitamente permessa** (articolo *Other Trading Activities* → «Automated
trading systems and trade copiers are permitted»), MultiCharts nella lista piattaforme,
e il trader risponde di errori e malfunzionamenti del proprio software.

| | |
|---|---|
| Profit target | **$3.000** |
| Max Loss Limit (MLL) | **$2.000** |
| Tipo di drawdown | **EOD trailing** sul massimo saldo di *chiusura* |
| Initial Trail Balance | $52.100 → superato, l'MLL **si blocca** |
| Locked MLL | $50.100 |
| Consistency | 50% (con cushion: si può passare in 2 giorni) |
| Size massima | 4 mini / 40 micro |
| Daily loss limit | **nessuno** (opzionale al checkout) |
| Commissioni | NQ **$1.75/lato**, MNQ **$0.50/lato**, GC $2.30, MGC $0.80 |

**Il trailing si ferma prima del target**: l'MLL insegue il saldo solo fino a $52.100, poi
si blocca a $50.100, mentre il target è $53.000. La fase a rischio è quindi solo il tratto
**dall'inizio ai primi $2.100 di profitto**; il resto si percorre contro un pavimento fisso.
È molto meno ostile del trailing continuo che avevamo assunto prima.

**Conti da NON usare**: *LucidDaily*, dove il news trading è un **hard breach** (flat da 1
minuto prima a 1 minuto dopo le news rosse). Le nostre strategie tengono posizione dalla
mattina alle 14:00 CT, quindi nei giorni di FOMC (13:00 CT) sarebbero in violazione.
Restano **Flex**, Pro e Direct.

**Niente Eurex** nella lista prodotti approvati (tutto CME/CBOT/NYMEX/COMEX) → il DAX
resta fuori, e con esso il Dax Trading Lab di Serafini.

**Attenzione ai costi in micro**: sviluppiamo su 1 NQ, dove il round turn costa $3.50. La
stessa esposizione in micro (10 MNQ) costa **$10.00**, cioè quasi il triplo. Quando lo
Stage 7 dimensiona in micro, i costi vanno ricalcolati con le tariffe MNQ: il backtest sul
mini li sottostima.

### Altre regole tenute come criteri di progetto

Da Apex, perché generalizzano: niente trade senza stop (conferma `StopPts` obbligatorio su
NQ First5); niente target minuscoli con stop enormi; flat prima della chiusura; **niente
hedging su strumenti uguali o correlati anche fra conti diversi**, che conferma e
irrigidisce il gate 8.

---

## Il criterio P/D — perché la size non salva una strategia (01/10/2026)

Lavoriamo a **lotti fissi**, senza compounding. Quindi con N contratti profitto e drawdown
scalano entrambi lineari: `P_N = N·P` e `D_N = N·D`, dove P e D sono profitto e drawdown
misurati **a 1 micro** sulla finestra di valutazione.

Per passare servono due condizioni insieme:

```
N · P  ≥  Target        →   N ≥ Target / P
N · D  ≤  MLL           →   N ≤ MLL / D
```

Una N valida esiste **se e solo se** `Target/P ≤ MLL/D`, cioè:

> **P / D  ≥  Target / MLL**

**N si semplifica.** Non compare nel criterio. Se il rapporto non regge, nessuna size lo
aggiusta: aumentare i contratti avvicina al target e al breach nella stessa proporzione.

### Conseguenza sulla scelta del conto

| Conto | Target | MLL | **Target/MLL** |
|---|---|---|---|
| 25k | $1.500 | $1.200 | **1,25** |
| **50k** | $3.000 | $2.000 | **1,50** |
| 100k | $6.000 | $3.000 | **2,00** |
| 150k | $9.000 | $4.500 | **2,00** |

Il conto più grande **non** è più facile: chiede un P/D doppio. Il 25k ha il rapporto
migliore ma un MLL di $1.200 che le nostre strategie NQ non reggono nemmeno a 1 micro
(drawdown misurato $1.502 ORB, $1.889 VaultBreak). **Resta il 50k**, come già scelto.

### Come si usa, e cosa NON dice

È uno **screening di fattibilità**, non una promessa. In particolare:

- usa il drawdown **storico su un singolo percorso**, non la coda Monte Carlo del Gate 3;
- **soprattutto: ignora la granularità.** Il criterio ammette N frazionari, ma il contratto
  minimo è 1 micro. Serve quindi una **seconda condizione indipendente**:

  > **D per 1 micro ≤ MLL** — anche la size minima deve sopravvivere.

  VaultBreak è il caso che l'ha resa evidente: P/D sulla coda MC = 2,34 ≥ 1,50, quindi il
  primo criterio **passa**; ma il drawdown a 1 micro è $3.109 contro $2.000, e non esiste
  mezzo micro. **Bocciata dalla seconda condizione.** Le due vanno verificate entrambe;
- ignora l'**EOD trailing**: nel tratto iniziale (fino a $2.100 di profitto) il pavimento si
  alza, quindi il margine reale è più stretto di MLL;
- ignora la **consistency 50%** e l'**ordine dei trade** (li copre il Monte Carlo);
- P e D vanno misurati sulla stessa finestra e con gli stessi costi.

> **Ritrattazione (01/10/2026).** Avevo derivato da qui una soglia «MC-robusta» di 3,86 sul
> 50k, moltiplicando `Target/MLL` per il 2,57× misurato sull'ORB. **Sbagliato: quel rapporto
> non è una costante.** Misurato su due strategie vale **2,56 (ORB)** e **1,67 (VaultBreak)**,
> entrambi come 95° percentile ÷ drawdown close-to-close. Dipende dalla forma della
> distribuzione dei trade — l'ORB, con perdite fino a $3.000 per il cap `MaxRisk_USD`, è molto
> più sensibile al reshuffle di VaultBreak, che ha la perdita bloccata a −$2.015. Nessuna
> scorciatoia: **il Monte Carlo va lanciato**, non stimato.

> Regola operativa: allo Stage 4 una variante si giudica sul **P/D**, non su avg trade / PF
> / drawdown presi singolarmente. `MaxTradesPerDay 1` migliorava tutte e tre e peggiorava
> il P/D — ed era sbagliata (vedi VaultBreak SPEC).

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
| max DD 1 contratto ÷ 10 (micro) | ≤ 50% dell'MLL → **≤ $1.000** (LucidFlex 50k) |
| peggior trade ÷ 10 | ≤ 25% dell'MLL → **≤ $500** (su Flex non c'è daily loss, quindi si àncora all'MLL) |
| tabella annuale | nessun anno > 50% del profitto; segno stabile 2021‑23 vs 2024+ |

## Stage 3 — Monte Carlo built‑in (IS)
Reshuffle 1000 sim, 100% trade; Distribution analysis.

**Gate 3**: mediana net profit > 0; < 10% simulazioni in perdita; DD 95° perc. ÷ 10
≤ MLL → **≤ $2.000** (LucidFlex 50k).

**Prerequisito sui costi**: il MC gira sulla lista trade del report, quindi eredita lo
slippage non addebitato. Il report di input va prodotto con lo **slippage incorporato nella
commissione** (`$2,50 + 1 tick`: **$7,50/lato su NQ**, $15,00 su ES), campo slippage a 0.
Addebita un tick anche sui target (che sono limit e non slitterebbero): è conservativo, ed
è l'unico modo per avere una lista trade corretta senza stimare nulla.

> Perché qui la soglia è il 100% dell'MLL e al Gate 2 era il 50%: il Gate 2 guarda **un
> solo percorso storico**, quindi il margine copre la coda ignota. Il 95° percentile del
> reshuffle **è già** la coda, quindi non serve margine sopra. Le due soglie misurano la
> stessa cosa con strumenti di qualità diversa.

>  **Regola d'ordine, violata due volte — Stage 3 viene PRIMA dello Stage 4.**
> Sull'ORB abbiamo ottimizzato tre varianti e poi il Monte Carlo l'ha uccisa: lavoro
> buttato. Su VaultBreak abbiamo rifatto lo stesso errore (`MaxTradesPerDay`, porting ES)
> con il Gate 3 mai lanciato. Il Monte Carlo è **economico** (gira sul report già in mano)
> e **decisivo**: va fatto appena il Gate 2 è chiuso, prima di spendere run su varianti.
> Se una strategia muore al Gate 3, ogni ora di Stage 4 spesa prima è tempo perso.

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

## Riaprire una strategia chiusa: quando sì e quando no (01/10/2026)

Domanda emersa dopo la chiusura di ORB e VaultBreak: **conviene rifarle long *e* short?**
Risposta: **no, non ora** — e la ragione tecnica è più interessante del verdetto.

1. **Il vincolo che le ha uccise è il rischio per trade, non la direzione.** Entrambe
   rischiano ~$200 per micro (stop 100 pt NQ): l'MLL da $2.000 sono 10 stop. Il 95°
   percentile a ~$3.110 vale ~26 perdite medie. Aggiungere un lato **aggiunge trade, non
   riduce l'unità di rischio**.
2. **Il Gate 3 è cieco proprio al beneficio che si spererebbe.** Il vantaggio di un lato
   short è *temporale*: guadagna quando il long sanguina. Ma il Monte Carlo a reshuffle
   **distrugge l'ordine dei trade** — assume che siano scambiabili. Una diversificazione che
   dipende da *quando* i trade accadono non compare nel 95° percentile. Anzi: a parità di
   edge per trade, più trade significano più occasioni per una brutta serie, quindi il
   percentile peggiora. Sotto questa metrica aggiungere lo short ha più probabilità di
   **danneggiare** che di aiutare.
3. **Non sarebbe una variante ma un'ipotesi nuova** → nuova spec Stage 0, non un
   ripescaggio. E abbiamo appena pagato due volte il prezzo di fare Stage 4 su cose che non
   avevano passato lo Stage 3.

**Condizione esplicita per riaprirle**: se NQ First5 — che è progettata con lo short e ha lo
stop parametrico — mostra allo Stage 2 che il lato short su NQ ha un edge reale, allora
riaprire ORB/VaultBreak long+short diventa un'ipotesi **informata** invece di un tentativo
di salvataggio. Prima di quel dato, no.

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
