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

> **Come si impostano davvero in MultiCharts** (stessa regola dello Stage 3, scoperta il
> 29/09/2026): lo slippage impostato nel campo apposito viene addebitato solo per una
> frazione del dovuto, perché MC lo limita al range della barra e con Bar Magnifier a 1
> minuto non resta spazio. Quindi lo slippage si **incorpora nella commissione** e il campo
> slippage si lascia a zero: su NQ `$2,50 + 1 tick da $5,00` = **`7.5$ per Contract`,
> slippage `0 ticks`**. Su ES sarebbe $15,00/lato.

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

## Il cimitero non è un bidone — e perché non si passa dallo Stage 5 (01/10/2026)

Domanda: *una strategia non dovrebbe arrivare almeno all'OOS prima di essere chiusa?*
**No, per costruzione** — ma la risposta va qualificata, perché il rischio che nasconde è
reale.

### Perché l'OOS non si spende sui bocciati

Lo Stage 5 si fa **una volta sola**: guardare l'OOS lo consuma. Spenderlo su una strategia
che già sappiamo non dimensionabile non aggiunge nulla e crea la tentazione peggiore —
usare l'informazione OOS per aggiustarla, che è contaminazione. L'ordine dei gate esiste
per mettere i test **economici e decisivi prima** di quelli costosi e irripetibili.

### Ma la *causa di morte* va registrata, perché non sono equivalenti

| causa | significato | recuperabile? |
|---|---|---|
| **A — edge assente** | expectancy negativa, split‑sample fallito, PF ≤ 1 | no |
| **B — non entra nel conto** | l'edge c'è, ma l'unità di rischio è troppo grande per l'MLL | **sì**, se cambiano conto, strumento o unità di rischio |

ORB e VaultBreak sono **B**, non A: positive in tutti e cinque gli anni e in entrambe le
metà. Non sono «strategie sbagliate», sono **incompatibili con 1 micro NQ su un MLL da
$2.000**. Verificato che non sia un artefatto della scelta del conto — per VaultBreak
(P = $7.262, D = $3.109 per micro) non esiste N intera su **nessuna** taglia Lucid:

| conto | serve N fra | esito |
|---|---|---|
| 25k | 0,21 e 0,39 micro | nessuna |
| 50k | 0,41 e 0,64 | nessuna |
| 100k | 0,83 e 0,96 | nessuna |
| 150k | **1,24 e 1,45** | nessuna — manca l'intero per un soffio |

**Regola**: ogni strategia chiusa resta archiviata **con i suoi report**. Se cambia il gate,
il conto o lo strumento, si ri‑testa in minuti — non si ricostruisce.

### La domanda metodologica aperta: il Gate 3 è il gate giusto?

Va messa per iscritto adesso, **mentre non conviene**, non quando farà comodo.

Il Gate 3 chiede: *nel 95% dei riordinamenti, 1 micro tenuto per cinque anni non sfonda
l'MLL*. Ma il problema reale della prop non è quello: è **arrivare a +$3.000 prima di
−$2.000**, su una finestra breve, con la possibilità di ripagare la fee e ritentare. È un
problema di **primo passaggio**, non di massimo drawdown quinquennale — e chi lo risolve è
lo **Stage 7**, che sta *dopo* il Gate 3 e che il Gate 3 impedisce di raggiungere.

In più il Monte Carlo a reshuffle assume i trade **scambiabili**: distrugge la struttura
temporale, quindi è severo con chi guadagna proprio dall'ordine in cui le cose accadono.

**Non si tocca adesso.** Rilassare un gate subito dopo due bocciature è esattamente la mossa
che ci siamo impegnati a non fare. Ma si fissa il **trigger**:

> Se **tutte** le candidate rimaste falliscono il Gate 3 pur avendo un edge (causa B), la
> conclusione non è «nessuna strategia funziona» ma **«il Gate 3 è mal specificato per il
> modello di business della prop»**. A quel punto si ri‑deriva la soglia dal problema di
> primo passaggio — una volta, su principio, prima di rivedere i numeri — e si ri‑passa
> **tutto il cimitero** nel gate nuovo.

Due su due sono già causa B. Il terzo dato lo darà NQ First5.

### Il terzo dato è arrivato — e non fa scattare il trigger (08/10/2026)

**NQ First5 è chiusa, causa B**, ma è morta al **Gate 2**, non al Gate 3: drawdown storico
**$5.004 per micro** contro una soglia di $1.000, con un edge chiaro sopra (294 trade, avg
$366,60 netto, PF 1,275 sulla versione filtrata). Il Monte Carlo non è stato lanciato: su un
report che sfonda di 5,8× sarebbe stato una formalità, visto che il 95° percentile è per
costruzione peggiore del drawdown storico.

| strategia | drawdown per micro | gate | causa |
|---|---|---|---|
| ORB Breakout | $3.121 — 95° pct MC | 3 | B |
| VaultBreak | $3.109 — 95° pct MC | 3 | B |
| **NQ First5** | **$5.004 — già storico** | **2** | **B** |

**Il trigger non scatta, e vale la pena essere precisi sul perché.** Dice *«tutte le
candidate rimaste»*: ne restano tre mai testate (VWAP Pullback, Gold Asian Range,
DriftPullback). Tre su tre fra quelle arrivate in fondo è un indizio forte, non la
condizione che avevamo scritto. Il trigger resta armato, invariato.

E c'è una ragione in più per non muoverlo adesso: **First5 non mette alla prova il Gate 3**.
Ha fallito una soglia diversa — il 50% dell'MLL sul drawdown *storico*, non l'MLL sul 95°
percentile — e l'obiezione metodologica che abbiamo scritto riguarda il secondo, non il
primo. Usarla come terza prova contro il Gate 3 sarebbe comodo e sbagliato.

**Quello che il terzo caso aggiunge davvero** è un dato nuovo, e peggiore della somma dei
primi due: per la prima volta la correzione **pre‑registrata come obbligatoria** si è
dimostrata insufficiente *prima ancora di girarla*. Il limite ottimistico calcolato sulla
lista trade — ogni perdita tagliata allo stop, nessun vincente toccato intrabar — resta
sopra soglia perfino con uno stop da 100 punti, che su uno strumento con ADR di sessione fra
300 e 600 è rumore. Non è che lo stop fosse tarato male: è che **tenere una posizione
direzionale per l'intera sessione su NQ costa $284 per micro di perdita media**, e il filtro
di regime che migliora l'edge lo aumenta, perché seleziona apposta le giornate più ampie.

La domanda che resta aperta non è quindi «il Gate 3 è troppo severo» ma una più scomoda:
**esiste su @NQ un edge intraday direzionale la cui unità di rischio stia sotto $200 per
micro?** Le tre candidate rimaste non sono tutte su NQ — Gold Asian Range è su GC — ed è un
motivo in più per testarle prima di toccare qualsiasi soglia.

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

### Il quarto dato capovolge il quadro: la prima morte per causa A (13/10/2026)

Le prime tre strategie morte lo erano tutte di **causa B** — edge presente, unità di rischio
troppo grande per l'MLL — e tutte su **@NQ**:

| | gate fallito | numero che uccide (per micro) |
|---|---|---|
| ORB | Gate 3 | DD 95° pct **$3.121** |
| VaultBreak | Gate 3 | DD 95° pct **$3.109** |
| NQ First5 | Gate 2 | DD storico **$5.784** |

Da lì era nata la domanda aperta: *esiste su @NQ un edge intraday direzionale la cui unità
di rischio stia sotto $200 per micro?* E Gold Asian Range era stata scelta apposta come
prima candidata **non su @NQ**.

**Gold ha risposto a una domanda diversa da quella che le avevamo fatto.** L'unità di
rischio **entra**: trade peggiore **$498 per MGC** contro una soglia di $500. Il muro di @NQ
non esiste su MGC. E la strategia muore comunque, di **causa A**: su 1.280 trade e cinque
anni l'intervallo di confidenza al 95% dell'avg trade **contiene lo zero** in entrambe le
varianti pre‑registrate (A: −$2…+$122, t = 1,89 · B: −$24…+$67, t = 0,92).

Non è una stima, è una dimostrazione: con una soglia di $140 netti e $25 di costo
andata‑ritorno su GC serve un edge **lordo** di $165 per trade, e ce ne sono **$85** e
**$46**. **Nemmeno azzerando i costi** si arriva alla soglia.

**Il trigger sul Gate 3 non scatta, e la ragione è importante.** Il trigger è armato per il
caso in cui *tutte* le candidate abbiano un edge e falliscano sull'unità di rischio: quello
sarebbe il segnale che il gate è mal specificato. Gold è l'esatto contrario — unità di
rischio dentro, edge fuori. Conta come **informazione a favore** dei gate così come sono,
non contro.

#### Le due cause sono davvero due cose diverse, e si vede adesso

Finora A e B erano una distinzione sulla carta. Con quattro dati si vede che selezionano
rimedi opposti:

- **causa B** → l'edge c'è, serve cambiare **strumento, taglia o conto**. È il motivo per cui
  le tre @NQ restano riapribili su un conto con MLL più largo.
- **causa A** → non c'è niente da ridimensionare. Cambiare strumento non crea un edge.
  **Definitiva.**

#### La lezione di metodo, che è un errore di lettura e non un gate da cambiare

Lo Stage 1 di Gold girava su quattro mesi del 2026 e dava numeri incoraggianti: avg trade
$89 per MGC, trade peggiore $442. Su cinque anni l'avg trade è **$2–6 per MGC**.

Il motivo è un regime di volatilità: **il range asiatico più largo di quattro mesi del 2026
(85,20 punti) supera il più largo dei cinque anni precedenti (49,50 punti)**. E lo stop *è*
l'ampiezza del range, quindi l'edge per trade scala con la volatilità realizzata **mentre i
costi restano fissi**. Con 39 punti di range i $25 di costo sono rumore; con 7 punti si
mangiano metà dell'edge lordo.

**Il Gate 1 non ha sbagliato**: chiede «meccanica corretta al 100%» e non ha mai preteso di
validare l'unità di rischio o l'edge. I numeri di rischio dello Stage 1 li ha letti come
buona notizia **l'analisi**, extrapolando da quattro mesi. Nessun gate va toccato; va
ricordato che **i numeri economici dello Stage 1 non sono un'anticipazione del Gate 2** e
che un'unità di rischio definita dalla volatilità realizzata va misurata sull'IS, non sul
campione recente.

#### Secondo errore di processo, registrato

Dopo il Gate 1 l'analisi aveva **scavalcato una pre‑registrazione**: la spec diceva «Gate 2
si giudica sulla variante B», e il risultato dello Stage 1 (WR della variante A al 57,7%
invece del 34% della ricerca) è stato usato per decidere che andassero **entrambe**. Su
cinque anni il WR della variante A è **42,6%**, vicino al 34% della ricerca.

La pre‑registrazione era giusta. Il campione che l'ha scavalcata era di **78 trade e quattro
mesi**. La regola che resta scritta: **una pre‑registrazione non si rivede su un campione
più piccolo di quello su cui verrà giudicata.**

### Due vincoli che tirano in direzioni opposte (14/10/2026)

Dalla ricerca v3 (`mc/ideas/candidate_lucidflex_50k_v3.md`), più due verifiche fatte qui.

#### 1. Il gate che morde è il drawdown, non il trade peggiore

Verificato con Monte Carlo indipendente (20.000 run per riga, esiti Bernoulli i.i.d.):
i gate sul drawdown — storico ÷10 ≤ $1.000 e 95° pct ÷10 ≤ $2.000 — implicano una
**perdita media per micro di circa $75–135**, secondo il PF e il numero di trade.

Il tetto di Gate 2 sul trade peggiore ($500 per micro) **non è mai il vincolo che stringe**:
chi passa i gate sul drawdown lo passa automaticamente. Tutto il lavoro fatto finora ragionava
sul numero sbagliato.

E incrociando con il pavimento dei costi: **a PF 1,20 la finestra è vuota**. Il drawdown
ammette al massimo 37–47 punti di R su MNQ, i costi ne richiedono almeno 53. Non esiste un R
che soddisfi entrambi. Serve **PF ≥ 1,30**, con margine 1,40.

Il gate formale resta `PF ≥ 1.2` e **non si riscrive**. Ma una candidata con PF atteso 1,2 va
considerata già fallita, e presentarla come «rispetta il gate» è fuorviante.

#### 2. Spostarsi su strumenti più piccoli non risolve: le due forze sono opposte

L'idea di portare una strategia morta per causa B su uno strumento con nozionale più piccolo
sembrava la via naturale. **Non lo è**, e il motivo è misurabile.

Confronto dei **tick contenuti in un range giornaliero** — quanti tick di costo entrano
nell'opportunità disponibile:

| | tick (pt) | ATR14 (pt) | tick per ATR | vs NQ |
|---|---|---|---|---|
| **NQ** | 0,25 | 260 | **1.040** | 1,00× |
| YM | 1,00 | 420 | 420 | 0,40× |
| RTY | 0,10 | 40 | 400 | 0,38× |
| GC | 0,10 | 30 | 300 | 0,29× |
| ES | 0,25 | 60 | 240 | **0,23×** |

*(ATR stimati e non verificati: da misurare su MC. Se cambiano, cambia la classifica.)*

**@NQ è lo strumento più fine di tutti.** Spostarsi altrove **migliora** il rapporto
rischio/MLL ma **peggiora** il rapporto costo/movimento, di un fattore da 2,5 a 4,3. Sono due
forze opposte, e il guadagno su un fronte si paga sull'altro.

Questo chiude una classe di idee di salvataggio, non una singola idea.

#### 3. Il porting di ORB e VaultBreak su MYM/M2K: falsificato in due minuti

La ricerca proponeva il porting come «candidata condizionale», con un test di falsificazione
eseguibile **senza nuovi backtest**: l'edge lordo per micro dopo il porting deve valere almeno
3 volte il costo per micro. Con ρ ≈ 0,40 (quanto vale in dollari un micro YM contro un micro
NQ, a pari ATR) e un costo per micro di ~$3, serve un **lordo su NQ ≥ ~$225 per contratto**.

Misurato sui report già in repo:

| | n | avg trade netto | **avg trade lordo** | lordo per micro dopo il porting | esito |
|---|---|---|---|---|---|
| ORB (IS 2020‑24, costi) | 827 | $81 | **$86** | $3,44 contro $3 di costo | ✖ |
| VaultBreak (Stage 2 IS) | 723 | $110 | **$115** | $4,60 contro $3 di costo | ✖ |

Servono $9 di lordo per micro. Ne abbiamo $3,44 e $4,60: mancano un fattore **2,6** e **2,0**.

**Il porting è morto prima di partire.** Ed è una conferma del punto 2: l'edge si rimpicciolisce
con il nozionale, i costi no.

#### 4. La finestra su MGC era vuota: la morte di Gold era prevedibile con l'aritmetica

Su MGC a PF 1,20 il drawdown ammette uno stop di ~10 punti ($100/micro) e i costi ne
richiedono ~21 ($206/micro). **Finestra vuota.** Gold Asian Range aveva uno stop mediano di
**39 punti**, quattro volte il tetto.

Si potevano calcolare questi due numeri **prima** di scrivere una riga di codice. È lo stesso
errore di lettura già registrato nel cimitero, visto da un'angolazione nuova: non solo i
numeri economici dello Stage 1 non anticipano il Gate 2, ma **esiste un calcolo a priori che
dice se una combinazione strumento/PF ha una finestra non vuota**, e va fatto allo Stage 0.

**Conseguenza per la pipeline**: allo Stage 0, prima di scrivere il codice, si calcola la
finestra dello stop per lo strumento scelto. Se è vuota, la spec non si scrive. Non è un gate
nuovo: è aritmetica che evita di spendere Stage 1 e Stage 2.

### Il numero che decide tutto, e non contiene lo strumento (15/10/2026)

Dalla ricerca v4, più la verifica fatta qui. **Corregge due cose che avevo scritto ieri in
questo stesso documento.**

#### L'eccesso sul caso: il metro giusto

Con stop S e target T, in un random walk senza drift la probabilità di toccare T prima di S
è **1/(1 + R:R)** — il «null». E il PF vale WR·R:R/(1−WR), quindi il WR richiesto per un dato
PF è **PF/(PF + R:R)**.

| R:R | null | WR per PF 1,3 | **eccesso richiesto** |
|---|---|---|---|
| 0,50 | 66,7% | 72,2% | **+5,6 pp** |
| 0,80 | 55,6% | 61,9% | **+6,3 pp** |
| 1,00 | 50,0% | 56,5% | **+6,5 pp** |

Nella banda 0,5–1 l'eccesso richiesto è quasi **costante**. Quindi **cambiare il rapporto
target/stop non crea edge: lo rietichetta.** (Sotto R:R 0,25 l'eccesso richiesto scende, ma
il target diventa più piccolo dei costi: escluso per un altro motivo.)

#### Le nostre sei, sullo stesso asse

| strategia | n | WR | R:R | null | **eccesso** | PF |
|---|---|---|---|---|---|---|
| **VaultBreak** | 723 | 63,1% | 0,730 | 57,8% | **+5,3 pp** | **1,246** |
| Gold A | 1.280 | 42,6% | 1,554 | 39,2% | +3,4 | 1,152 |
| ORB | 827 | 55,6% | 0,898 | 52,7% | +2,9 | 1,126 |
| Gold B | 1.280 | 52,7% | 0,955 | 51,2% | +1,5 | 1,062 |
| VWAP filtro | 605 | 72,9% | 0,393 | 71,8% | +1,1 | 1,075 |
| VWAP base | 764 | 56,3% | 0,789 | 55,9% | **+0,4** | 1,022 |

Serve **+5,6…+6,5 pp**. Il nostro massimo è **+5,3** (VaultBreak). La ricerca v4 trova che la
letteratura documenta **+1,5…+5 pp** per le famiglie intraday sugli indici: siamo in linea
con la letteratura, e la letteratura non basta.

#### La formula di fattibilità, senza strumento

Due vincoli stringono R da lati opposti:

- **costi**: R ≥ (soglia_avg_trade + costo) / E
- **drawdown**: R ≤ DDcap / (DD/R)

dove E è l'edge lordo in unità di R e **DD/R è il drawdown in multipli di R**. Fattibile se:

```
RATIO = E × DDcap / (DD_R × (soglia + costo))  ≥  1
```

| strategia | E | DD/R | R ammesso dal DD | R richiesto dai costi | **RATIO** |
|---|---|---|---|---|---|
| **VaultBreak** | 0,0952 | 25,6 | $78 | $95 | **0,83** |
| ORB | 0,0597 | 21,5 | $93 | $151 | 0,62 |
| Gold A | 0,1239 | 63,8 | $31 | $73 | 0,43 |
| VWAP filtro | 0,0292 | 19,6 | $102 | $308 | 0,33 |
| Gold B | 0,0636 | 64,6 | $31 | $142 | 0,22 |
| VWAP base | 0,0253 | 50,0 | $40 | $356 | 0,11 |

*(DDcap $2.000 = Gate 3. Soglia $7/micro = Gate 2 avg trade ÷ 10. Costo micro $2 stimato.
Per Gold il DD 95° non è mai stato misurato: uso il DD storico × 2 come proxy prudente.)*

**Tutte e sei sotto 1.** La migliore, VaultBreak, manca del **17%**.

#### Correzione 1: il porting non è morto per il motivo che avevo scritto

Ieri avevo falsificato il porting di ORB/VaultBreak su MYM calcolando che l'edge si
rimpicciolisce con ρ ≈ 0,40 (il rapporto fra il valore in dollari di un micro YM e uno NQ).
**Quel calcolo è sbagliato.** Assume di tenere lo stop alla stessa *frazione di ATR*; se
invece si tiene R allo stesso *valore in dollari*, l'edge in dollari non cambia.

Il porting è comunque morto, ma per un motivo più forte e più generale: **DD/R non dipende
dallo strumento.** È una proprietà della distribuzione dei trade. Quindi cambiare strumento
cambia R in dollari ma non il drawdown in multipli di R: si può sempre rimpicciolire R per
passare il gate sul drawdown, ma così si rimpicciolisce l'edge in dollari **mentre il costo
resta fisso**. La formula sopra lo dice in un numero.

**Nessun cambio di strumento ha mai potuto salvare nessuna delle sei.**

#### Correzione 2: la misura «tick per range giornaliero» era il metro sbagliato

Ieri avevo scritto che @NQ è lo strumento più fine (1.040 tick per ATR contro 420 di YM) e
che spostarsi altrove peggiora il rapporto costo/movimento. **Non è vero**, e l'errore è
identificabile: ho misurato la finezza del tick **in punti**, che non è confrontabile fra
strumenti con valore del punto diverso. Un tick di MYM e uno di MNQ valgono **entrambi
$0,50**. In dollari sono identici, quindi la «grossolanità» di YM non si traduce in un costo
maggiore.

Le due quantità che decidono sono invece: **il costo in unità di R** (dipende solo dal costo
in dollari) e **R/ATR** (quanto spazio ha lo stop rispetto al rumore). Su entrambe MYM e M2K
battono MNQ: al budget di $100 per micro, R vale **0,19 ATR su MNQ** e **0,48 ATR su MYM**.
La ricerca v4 aveva ragione e la tabella dei tick va letta come superata.

#### Il limite ottimistico su VaultBreak, che chiude la candidata migliore

VaultBreak è l'unica con un RATIO sopra 0,8. Azzerando **del tutto** i costi del micro, il
suo R richiesto scende da $95 a $73,5 e il RATIO sale a **1,06**.

Cioè: **VaultBreak è fattibile solo a costi esattamente zero.** Non è un margine, è il
confine. Con un costo anche di $1 andata‑ritorno per micro il RATIO è 0,93.

#### Che cosa resta da cercare, detto in numeri

Non serve un altro strumento e non serve un altro rapporto target/stop. Serve **una delle
due**:

| | oggi (il nostro massimo) | serve |
|---|---|---|
| **E**, edge lordo in unità di R | 0,0952 | **≥ 0,115** (+21%) |
| **DD/R**, drawdown in multipli di R | 25,6 | **≤ 21** (−18%) |

Il secondo è interessante perché **non richiede più edge**: un DD/R più basso si ottiene con
una distribuzione di P&L meno dispersa — meno uscite a tempo parziali, più esiti binari
stop/target. È una proprietà del disegno delle uscite, non dell'ipotesi di mercato.

Nota tecnica che vale la pena tenere: il Monte Carlo su esiti binari ±R prevedeva DD di
9–11 R per questi profili, e il DD misurato è **25,6 R**. La differenza non è il clustering:
è che i P&L reali sono **dispersi** fra 0 e R, non binari, e la varianza per trade è più
alta. **I Monte Carlo su esiti binari sottostimano il drawdown di circa 2,5 volte.**

### Gli ATR misurati, finalmente (15/10/2026)

`mc/strategies/ATR_Window_Study.txt` su cinque strumenti, **1.692–1.750 giorni ciascuno,
2020‑01‑02 → 2026‑10‑14**, finestra RTH definita dal codice. Log in
`mc/docs/measures/atr_window_rth_2020-2026.txt`.

#### Specifiche lette da MC, non dalla memoria

| | tick | bpv (big) | tick in $ (big) | **tick in $ (micro)** | **$/punto micro** |
|---|---|---|---|---|---|
| NQ | 0,25 | 50 → **20** | $5,00 | **$0,50** | **$2,00** |
| ES | 0,25 | **50** | $12,50 | **$1,25** | **$5,00** |
| YM | 1,00 | **5** | $5,00 | **$0,50** | **$0,50** |
| RTY | 0,10 | **50** | $5,00 | **$0,50** | **$5,00** |
| GC | 0,10 | **100** | $10,00 | **$1,00** | **$10,00** |

I valori del punto che usavo erano **giusti**. Ma il dato nuovo è il **tick in dollari sul
micro**: MNQ, MYM e M2K costano **$0,50**, MGC $1,00, **MES $1,25**. MES è 2,5 volte gli
altri. Questo chiude definitivamente la questione del metro: la «grossolanità» del tick in
*punti* non significa niente, il tick in *dollari* sì.

#### Range RTH mediano per anno, in punti

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | **2020‑24** |
|---|---|---|---|---|---|---|---|---|
| NQ | 184,5 | 175,5 | 290,1 | 186,5 | 224,2 | 270,2 | 367,0 | **210,0** |
| ES | 41,5 | 35,8 | 69,6 | 41,1 | 43,2 | 58,5 | 64,2 | **44,8** |
| YM | 347,0 | 283,0 | 477,5 | 303,5 | 329,0 | 420,0 | 472,0 | **339,0** |
| RTY | 30,1 | 35,8 | 39,8 | 27,9 | 31,1 | 31,9 | 37,5 | **32,5** |
| GC | 19,4 | 16,1 | 16,2 | 15,6 | 21,3 | 34,8 | 59,8 | **17,8** |

**Le mie stime erano tutte troppo alte:**

| | mia stima | misurato | errore |
|---|---|---|---|
| NQ | 260 | 210,0 | **−19%** |
| ES | 60 | 44,8 | **−25%** |
| YM | 420 | 339,0 | **−19%** |
| RTY | 40 | 32,5 | **−19%** |
| **GC** | 30 | **17,8** | **−41%** |

#### Il cambio di regime, quantificato

Rapporto fra il range mediano dell'anno e quello del 2020‑2024:

| | 2025 | **2026** |
|---|---|---|
| **GC** | 1,96× | **3,36×** |
| NQ | 1,29× | **1,75×** |
| ES | 1,31× | 1,44× |
| YM | 1,24× | 1,39× |
| **RTY** | 0,98× | **1,15×** |

**Il 2026 dell'oro vale 3,36 volte il suo regime normale.** È la versione misurata di quello
che ha reso illeggibile lo Stage 1 di Gold Asian Range: il range asiatico di 39 punti del
2026 corrisponde a **circa 11–12 punti nel 2020‑2024**, cioè **$110–120 per MGC** —
*dentro* il budget. Entrambe le letture che ne avevo dato (prima «$442 di trade peggiore,
ottima notizia», poi «$378 contro un budget di $200, muro strutturale») erano sbagliate, e
per la stessa ragione: misuravano un regime 3,36 volte anomalo.

**RTY è lo strumento più stabile fra i regimi** (1,15× nel 2026, 0,98× nel 2025). Per una
strategia il cui rischio dipende dalla volatilità realizzata, è una proprietà che vale.

#### La classifica degli strumenti, con i numeri misurati

R/ATR al budget di rischio consentito dai gate sul drawdown ($60–110 per micro):

| micro | $/pt | ATR 20‑24 | R=$60 → ATR | R=$110 → ATR | tick $ micro |
|---|---|---|---|---|---|
| **M2K** | $5,00 | 32,5 | **0,37** | **0,68** | $0,50 |
| **MYM** | $0,50 | 339,0 | **0,35** | **0,65** | $0,50 |
| MGC | $10,00 | 17,8 | 0,34 | 0,62 | $1,00 |
| MES | $5,00 | 44,8 | 0,27 | 0,49 | **$1,25** |
| **MNQ** | $2,00 | 210,0 | **0,14** | **0,26** | $0,50 |

**M2K e MYM vincono su entrambi gli assi**: lo stop ha il doppio dello spazio rispetto al
rumore che ha su MNQ, allo stesso costo per tick. **MNQ è l'ultimo**, e questo è il numero
che spiega le tre morti su @NQ: al budget consentito, lo stop vale **0,14–0,26 ATR**, cioè
sta dentro il rumore.

MGC è meglio di come l'avevo giudicato (l'ATR reale è il 41% più basso della mia stima), ma
il tick costa il doppio. MES è il peggiore per costo.

#### La soglia di E per strumento, che è il criterio operativo

Da `RATIO = E × DDcap / (DD_R × (soglia + costo)) ≥ 1`, con DDcap $2.000 e soglia $7/micro:

| micro | costo A/R | E richiesta a DD_R 25,6 | a DD_R 21 | a DD_R 15 |
|---|---|---|---|---|
| **M2K / MYM / MNQ** | $2,00 | **0,1152** | **0,0945** | 0,0675 |
| MES | $3,50 | 0,1344 | 0,1103 | 0,0788 |
| MGC | $3,60 | 0,1357 | 0,1113 | 0,0795 |

VaultBreak, la nostra migliore, ha **E = 0,0952 con DD_R = 25,6**. Quindi:

- su M2K/MYM servirebbe **E ≥ 0,1152**: manca il **21%**
- **a DD_R = 21 la soglia scende a 0,0945 e VaultBreak passerebbe** (RATIO 1,007)
- su MES e MGC la soglia sale del 17–18%: **da evitare**

**Il criterio operativo per lo Stage 0, d'ora in poi**: una candidata su M2K o MYM deve
promettere **E ≥ 0,115** con DD_R ≈ 25, oppure **E ≥ 0,095** se il disegno delle uscite
tiene DD_R sotto 21. Tutto il resto — strumento, rapporto target/stop, finestra oraria — è
secondario a questi due numeri.

### La sesta morte è la più informativa: un edge vero non basta (15/10/2026)

DriftPullback è chiusa al Gate 2 con **t = 3,01 su 3.499 trade**. È la **prima strategia
della pipeline con un edge statisticamente solido**, e non passa.

| strategia | n | **t** | E | DD_R | **RATIO** | causa |
|---|---|---|---|---|---|---|
| **DriftPullback** | 3.499 | **3,01** | 0,0543 | 25,5 | **0,47** | **B** |
| VaultBreak | 723 | — | 0,0952 | 25,6 | 0,83 | B |
| ORB | 827 | — | 0,0597 | 21,5 | 0,62 | B |
| Gold A | 1.280 | 1,89 | 0,1239 | 63,8 | 0,43 | A |
| VWAP filtro | 605 | 0,69 | 0,0292 | 19,6 | 0,33 | A |
| Gold B | 1.280 | 0,92 | 0,0636 | 64,6 | 0,22 | A |
| VWAP base | 764 | 0,23 | 0,0253 | 50,0 | 0,11 | A |

**Il criterio chiede E ≥ 0,115. DriftPullback ha E = 0,0543 con t = 3,01.**

> Un edge statisticamente solido è ancora **2,1 volte troppo piccolo** per questo conto.

E il limite ottimistico lo chiude senza appello: con DD_R 25,5 il drawdown ammette
R ≤ $78 per micro, dove l'edge lordo vale $4,24 — contro i $7 richiesti. **Anche a costi
esattamente zero manca un fattore 1,65.**

#### Una regola nuova, da una mia previsione sbagliata

Avevo previsto che il WR salisse dal 64,4% del 2026 al 70% sull'IS, perché lo stop fisso di
80 punti vale 0,38 ATR nell'IS contro 0,22 nel 2026. Misurato: **63,5%**, invariato.

L'errore: guardavo solo lo stop, ma **il target è fisso anch'esso**. La probabilità di primo
tocco è **S/(S+T)**, che dipende dal *rapporto* e non dalla scala.

> **Quando stop e target sono entrambi fissi in punti, il win rate è invariante al regime di
> volatilità.** Cambia il tempo di risoluzione, non l'esito.
>
> È il contrario del caso Gold, dove lo stop *era* il range — scalava con la volatilità —
> mentre i costi restavano fissi. Là il regime cambiava tutto; qui niente.

Conseguenza pratica: **il regime va invocato solo quando una delle due gambe scala con la
volatilità e l'altra no.** Non è un argomento generico da usare per sospendere un verdetto.

#### Dove siamo, detto senza addolcirlo

Sei strategie, sei morte. Quattro di causa B (edge presente, conto troppo piccolo) e due di
causa A (edge assente). Il RATIO migliore mai raggiunto è **0,83** (VaultBreak), e l'edge più
solido mai misurato è **t = 3,01** con un RATIO di **0,47**.

Le due cose non coincidono: **la strategia con l'edge più credibile non è quella col RATIO
più alto.** VaultBreak ha E quasi doppia ma solo 723 trade; DriftPullback ha metà E su 3.499
trade. Nessuna delle due arriva a 1.

**Il trigger sul Gate 3 non scatta** — resta armato per il caso in cui *tutte* le candidate
abbiano un edge e cadano sul rischio. Siamo a quattro su sei, e due sono morte senza edge.
Ma la domanda che ne esce è la stessa di quel trigger, posta meglio: se un edge con
**t = 3,01** non passa, il problema è il rapporto fra l'MLL di $2.000 e il target di $3.000,
non il catalogo delle strategie.

## 🔔 Il trigger sul Gate 3 è scattato (15/10/2026)

Il trigger era armato il 01/10 con queste parole: «*se tutte le candidate falliscono il
Gate 3 pur avendo un edge, allora il gate è mal specificato, si ri-deriva dal primo passaggio
e si ri-passa tutto il cimitero*». Quattro delle sei sono morte di **causa B** — edge
presente, rischio fuori budget. La condizione è soddisfatta.

Ma non è scattato per conteggio: è scattato perché c'è **un numero**.

### VaultBreak passa l'eval vera con il 90% di probabilità

Simulazione di **primo passaggio** sul P&L giornaliero misurato dell'IS 2020‑2024, 2.000
riordinamenti dei giorni: raggiungere **+$3.000 prima di −$2.000 dal picco**.

| rischio per trade | P(passa) | giorni mediani |
|---|---|---|
| **VaultBreak $120** *(= 1 micro, la strategia così com'è)* | **90,0%** | **141** |
| VaultBreak $150 | 83,8% | 101 |
| DriftPullback $120 | 63,6% | 137 |
| GoldA $120 | 56,6% | 109 |
| ORB $120 | 49,2% | 221 |

**La size minima è 1 micro**, e la perdita media realizzata di VaultBreak è **$121 per
micro**: quindi la riga a $120 non è una taratura, è **la strategia senza modifiche**.

Sul percorso storico, nell'ordine vero: a $120 arriva a +$3.000 in **181 giorni operativi**
con un drawdown massimo trailing di **$1.759** — sotto l'MLL di $2.000.

### Perché il Gate 3 la vietava

Gate 3 chiede: DD al 95° percentile su cinque anni ÷ 10 ≤ $2.000. VaultBreak dava **$3.109**.
Giusto — su cinque anni quel drawdown esiste.

**Ma l'eval non chiede di sopravvivere cinque anni.** Chiede +$3.000 prima di −$2.000, e
questo accade in **141 giorni mediani**. La strategia **finisce prima** che il drawdown grande
abbia il tempo di formarsi.

Il Gate 3 misura la sopravvivenza di un conto tenuto aperto per sempre. L'eval è un problema
di **primo passaggio** su una finestra breve, con la possibilità di ritentare. Sono due
domande diverse, e il gate risponde a quella sbagliata.

### Quattro cautele, nessuna delle quali ho risolto

1. **È tutto in-sample.** VaultBreak è morta al Gate 3, quindi **l'OOS non è mai stato
   lanciato**. Questi numeri vengono dal 2020‑2024 su cui la strategia era già stata
   ottimizzata allo Stage 4. **Non sono una previsione.**
2. **Il riordinamento è un limite superiore.** Rompe il raggruppamento delle perdite, che su
   un breakout @NQ è reale (le perdite si addensano nei regimi laterali). Il 90% va letto
   come il massimo ottenibile, non come la stima centrale.
3. **MLL semplificata**: non ho modellato il blocco a $50.100 (che renderebbe le cose più
   facili) né la regola di consistenza al 50% (che le renderebbe più difficili).
4. **Non riscrivo i gate.** Il trigger dice di ri-derivare il criterio dal primo passaggio e
   di ri-passare il cimitero: è una decisione dell'utente, non mia. Qui c'è l'evidenza, non
   la modifica.

### Il passo che decide, ed è uno solo

**L'OOS di VaultBreak su 2025‑2026.** È un run. Se il primo passaggio tiene fuori campione,
il Gate 3 va ri-derivato e il cimitero va ri-aperto per le quattro di causa B. Se non tiene,
il Gate 3 aveva ragione e il trigger si disarma.

Non serve altro prima di quello.

### E il basket non è la strada — misurato, non supposto

Correlazione dei P&L giornalieri: **Gold è indipendente da tutto** (−0,12…+0,00), ma il
blocco @NQ è a **0,39–0,50**. Sei strategie valgono **due fonti indipendenti**, non cinque.

E peggio: **ogni basket è peggiore del suo miglior componente singolo.**

| basket | n | E | R max ammesso | RATIO |
|---|---|---|---|---|
| VaultBreak da sola | 723 | 0,0952 | $60 | **0,63** |
| VaultBreak + GoldA | 2.003 | 0,1135 | **0** | 0,00 |
| tutte e cinque | 7.093 | 0,0685 | **0** | 0,00 |

Il motivo non l'avevo previsto: **il costo fisso scala col numero di trade, il budget di
drawdown no.** Un basket da 6.329 trade porta **$12.658 di costi** contro un budget di
drawdown di $1.000. Aggiungere strategie aggiunge più costo che diversificazione.

**Lo Stage 8 va quindi ripensato**: non come somma di strategie deboli, ma come scelta della
*meno* frequente fra quelle che passano il primo passaggio.

## La pipeline è troppo selettiva, e si può dire su quali assi (15/10/2026)

Obiezione dell'utente: 7,5 mesi per un payout non sono sostenibili, e il documento
`8. Livestreaming/1. live001_propfirm_deck-2_.pdf` dice di **ingegnerizzare il passaggio e
il payout**, non di renderlo un'utopia. *(Il deck è fatto di immagini e non ho potuto
leggerlo: va riletto e confrontato con quanto segue.)*

### Il nostro criterio ottimizza la cosa sbagliata

| | il nostro gate | il business |
|---|---|---|
| rischio per trade | DD ÷10 ≤ $1.000 → **spinge in basso** | **alto**, se la quota per tentativo è bassa |
| frequenza | **n ≥ 200** | **bassa**: ogni trade paga $2 contro un budget di $2.000 |
| drawdown a 5 anni | vincolo binding (Gate 3) | **irrilevante**: il conto dura settimane |

Il Gate 3 misura la sopravvivenza di un conto tenuto aperto per sempre. L'eval è un
**primo passaggio ripetibile**: +$3.000 prima di −$2.000, e se fallisci ricominci.

### Il numero: alzare il rischio accorcia il tempo più di quanto abbassi la probabilità

VaultBreak, primo passaggio su 2.500 riordinamenti, con riprova dopo ogni bust:

| rischio/trade | P(passa) | mesi se passa | **mesi se fallisce** | mesi attesi/payout |
|---|---|---|---|---|
| $120 *(dove il Gate 3 ci spinge)* | 91,5% | 6,6 | 4,7 | **7,0** |
| $200 | 73,3% | 2,9 | 2,3 | 3,7 |
| $400 | 55,8% | 1,0 | 0,9 | 1,6 |
| $600 | 51,6% | 0,6 | 0,6 | **0,9** |

La colonna che cambia tutto è **«mesi se fallisce»**: un tentativo andato male costa **meno
tempo** di uno riuscito. Quindi provare in fretta e accettare i bust domina, se la quota per
tentativo è bassa.

### L'ottimo dipende dalla quota per tentativo, che non conosciamo

Costo atteso per payout = **quota / P + €36/mese × mesi attesi** (€36 = solo il datafeed):

| quota/tentativo | R ottimo | P(passa) | mesi attesi | costo/payout |
|---|---|---|---|---|
| €50 | $750 | 50,4% | 0,6 | €121 |
| **€100** | **$600** | **52,9%** | **0,9** | **€220** |
| €150 | $400 | 57,7% | 1,5 | €314 |
| €200 | $200 | 74,6% | 3,7 | €400 |
| €500 | $150 | 84,5% | 5,2 | €779 |

**Serve il numero vero della quota LucidFlex per tentativo.** Senza quello non c'è un ottimo:
a quota zero conviene rischiare tutto in un trade, che è una lotteria, non ingegneria.

### Il vincolo che pone il tetto, e non è il drawdown

La **regola di consistenza al 50%** (nessun giorno oltre metà del profitto). Verificata sui
percorsi che passano:

| rischio/trade | miglior giorno (mediana) | passaggi che violano il 50% |
|---|---|---|
| $120 | 9% | 0% |
| $400 | 30% | 0% |
| **$600** | **43%** | **0%** |
| $850 | 55% | **66%** |

**Il tetto vero è intorno a $600–700 per trade**, e lo mette la consistenza, non il
drawdown. A $600 il miglior giorno vale già il 43%: è il bordo.

### Quindi: la pipeline è troppo selettiva, ma non va "allentata"

Va **ri-derivata su tre assi**, e su due va resa *più* severa:

1. **Gate 3**: sostituire «DD 95° pct su 5 anni ≤ $2.000» con **«costo atteso per payout»**,
   che è calcolabile e che dipende dalla quota per tentativo.
2. **Gate 2, `n ≥ 200`**: va **rovesciato**. Era pensato per la significatività statistica,
   ma nel conto reale ogni trade è un costo contro un budget di drawdown fisso. La
   significatività va misurata col **t-stat**, non col conteggio.
3. **Il tetto al rischio** va dalla **consistenza al 50%**, non dal drawdown a 5 anni.

### Quello che NON va toccato, e che non abbiamo mai verificato

Tutto questo vale **solo se l'edge esiste fuori campione**. Ogni numero qui sopra è
**in-sample**, sul 2020‑2024 su cui VaultBreak era già stata ottimizzata allo Stage 4. E
**nessuna delle sei strategie ha mai avuto un run OOS**, perché morivano prima.

A rischio alto l'errore di stima si amplifica: a $600 per trade, se l'edge fuori campione è
metà di quello in campione, P(passa) crolla e la quota si paga due volte. **L'OOS non è un
gate da allentare: è il solo che non abbiamo mai eseguito.**

### Tre cose, in ordine

1. **La quota per tentativo di LucidFlex.** Tutto l'ottimo pivota su quel numero.
2. **Rileggere il deck** `live001_propfirm_deck-2_.pdf` e confrontarlo con questa analisi:
   se il corso dice la stessa cosa, la ri-derivazione ha due fonti indipendenti.
3. **L'OOS di VaultBreak su 2025‑2026**, un run. È l'unica cosa che rende reale tutto il
   resto, ed è anche l'unica che può chiuderlo.
