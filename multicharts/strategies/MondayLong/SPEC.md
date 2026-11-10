# SPEC — MondayLong, ES → MES (Stage 0, 10/11/2026)

**Ipotesi**: il lunedì l'S&P 500 sale più spesso di quanto scenda. Si compra alla chiusura della
barra delle 19:00 CT della domenica, la prima ora piena della sessione Globex che appartiene al
lunedì, e si esce alle 15:55 CT del lunedì. Nessun filtro: è la famiglia "long del lunedì" nella
sua forma nuda, con l'unica aggiunta di uno stop sul prezzo.

**Perché**: due letture, nessuna delle due forte.
- *Effetto weekend inverso* (Brusa, Liu, Schulman 2005): dalla fine degli anni '80 sulle large
  cap il rendimento del lunedì non è più negativo ma positivo, soprattutto dopo un venerdì in
  rialzo. È la lettura più vicina a questo trade: ES è un indice di large cap.
- *Cambio dell'ora legale* (Kamstra, Kramer, Levi 2000): il paper chiedeva uno **short** nel
  lunedì dopo il cambio d'ora, due settimane l'anno. L'autore del codice scrive che "la zona
  selezionata è diventata Monday long": la finestra 19:00 → 15:55 è uscita da una ricerca su
  orari, non dal paper. Il paper non sostiene questo trade, lo ha solo ispirato.

Il meccanismo plausibile è un flusso: chi alleggerisce il venerdì per non portare rischio nel
weekend ricompra il lunedì, e lo fa dopo aver visto che il weekend non ha portato notizie.

**Chi perde**: chi vende nella Globex sottile della domenica sera e chi si è coperto per il
weekend e ricopre il lunedì a prezzi più alti. Lo diciamo come ipotesi: non abbiamo un modo di
misurarlo.

**Fonte**: "Triple Open", The Bridge del corso,
`protocollo/9.TheBridge/STRATEGIES/PROP FIRM COMPLEMENTARY/`: `1. Monday Long ES (EMA distance
filter).txt` (L644ES, v2.1), `1. Monday after an up Friday ES.txt` (L656ES), `1. Monday Long NQ
(ADX filter).txt` (L644NQ) e la scheda `1. Triple_Open.pdf`. I file originali restano lì e non si
toccano. La nostra versione è lo scheletro di L644ES **senza il filtro EMA** e **con uno stop**.

## Cosa la distingue da quello che è già stato provato

- **Overnight drift** (chiuso, gli autori lo danno per morto dopo il 2021) è il parente più
  vicino: questo trade tiene la domenica sera e la notte del lunedì, e quel pezzo **è** overnight
  drift. La differenza: qui si tiene una volta a settimana, dentro una sola sessione, e si porta
  anche tutta la RTH del lunedì. È un effetto di giorno della settimana, non di ora del giorno. Se
  l'overnight drift è morto, una parte di questo è morta con lui: il profilo per anno lo dirà
  (vedi Rischi), ma non lo si usa per cambiare le regole.
- **Last Half-Hour**: effetto di calendario intraday morto dopo la pubblicazione. Stesso rischio
  qui: weekend e ora legale sono effetti pubblicati da più di vent'anni e la scheda dell'autore
  lo scrive da sola ("calendar anomalies decay", 2024 quasi piatto).
- **Ciclo settimanale lunedì-mercoledì** di un altro corso: trascritto, mai testato. Nessun
  numero da cui partire.
- **DriftPullback e Overnight Bias ORB**, nel book, tradano NQ anche il lunedì in RTH. Questo è
  long ES nelle stesse ore del lunedì: la correlazione col book è il punto del gate (fase 3b),
  non un dettaglio.

## Regole

| | |
|---|---|
| Famiglia | calendario · giorno della settimana · solo long |
| Strumento · TF · sessione | @ES (sviluppo) → **MES** · **5 min** · CME Globex **17:00-16:00 CT senza pause**, timezone **Exchange (CT)**, barre timbrate alla chiusura · Bar Magnifier **1 min** |
| Armamento | nessun filtro. La sessione è quella del lunedì (una barra dopo le 16:30 CT appartiene alla sessione del giorno dopo, come nel codice dell'autore) e il lunedì **non** è un festivo NYSE né una chiusura anticipata |
| Trigger | **Buy this bar on close** sulla barra delle **19:00 CT** della domenica (la barra 18:55-19:00). Una volta a settimana, solo se flat |
| Exit | **stop 90 punti** sul prezzo d'ingresso, attivo dalla prima barra dopo l'ingresso (l'ingresso è sulla chiusura della barra delle 19:00, quindi non c'è barra scoperta) · **target +100 punti**, backstop come nell'originale · **uscita a tempo** alla chiusura della barra delle **15:55 CT** del lunedì (`Sell this bar on close`), con la barra delle 16:00 come rete se la 15:55 manca |
| Guardrail | max 1 trade a settimana, mai due posizioni. Nessun trade se il lunedì è festivo o a chiusura anticipata |
| Trade/giorno | 0-1 (un trade per sessione del lunedì; nella List of Trades l'ingresso porta la data della **domenica**) |
| Profilo atteso | WR 55-62%, R:R (vincita media / perdita media) intorno a 1, perdita massima per trade fissata dallo stop |

**Festivi.** Esclusi i lunedì in cui la NYSE è chiusa (Capodanno osservato, Martin Luther King,
Presidents' Day, Memorial Day, Juneteenth dal 2022, 4 luglio osservato, Labor Day, Natale
osservato) o chiude alle 13:00 ET (3 luglio se lun-gio; 24 dicembre se lun-gio). Il calendario si
calcola per regola come nel blocco "HOLIDAY CALENDAR" di L644ES v2.1, che si può riprendere così
com'è (incluso il calcolo della Pasqua, che non tocca i lunedì ma non dà fastidio). Le chiusure
straordinarie (lutto nazionale) non sono gestite, come nell'originale: nel 2020-2026 nessuna è
caduta di lunedì.

**Conteggio atteso dei trade** (calcolato dal calendario, non dai dati):
**IS 2020-2024: 232 lunedì** tradabili su 261 (29 esclusi). OOS 01/01/2025 → 09/11/2026:
89. Uno o due in meno sono possibili se mancano barre nei dati; di più è un bug.

**Lo stop è l'unica modifica rispetto all'originale**, che non ha stop (`StopPts 0`). Non viene
dai dati: viene dalla regola della via B, trade peggiore ≤ $500 per micro (conti sotto).

**IS**: 2020-01-01 → 2024-12-31 · **OOS**: 2025-01-01 → oggi.
Non serve lead-in: niente indicatori. Il calendario dei festivi si costruisce sulla prima barra di
ogni anno, per l'anno e il successivo.

## Conti (1 contratto; ES = $50/pt, MES = $5/pt)

Costi: **$15 per lato** nel campo commissione di @ES, slippage incluso, slippage di MC a 0 →
**$30 a giro per ES, $3 per MES**.

| | punti ES | @ES | MES |
|---|---|---|---|
| Stop | 90 | $4.500 + $30 = **$4.530** | **$453** |
| Target | 100 | $5.000 − $30 = **$4.970** | **$497** |
| Margine sotto il tetto di via B ($500 per micro) | 9,4 | $470 | **$47** |
| **Worst day** (un trade, uno stop) | | **$4.530** | **$453** |

**Perché 90 e non 99.** $500 per micro = $5.000 per ES = 100 punti lordi. Tolti $30 di costi il
massimo teorico è 99,4 punti. Con 90 restano 9,4 punti di ES (circa 37 tick) di margine per lo
slippage dello stop: nel backtest con Bar Magnifier lo stop si riempie al suo prezzo salvo che la
barra a 1 minuto apra già oltre; dal vivo la domenica sera il book è sottile. 95 punti
lascerebbero 4,4 punti, troppo poco per un ordine stop in Globex notturna. 90 è fissato qui e non
si tocca.

**Il trade non attraversa la pausa delle 16:00-17:00 CT**: entra dopo la riapertura della
domenica (il gap del weekend è già nel prezzo d'ingresso, lo stop non lo vede mai) ed esce alle
15:55 del lunedì. Per una prop che conta il giorno per sessione 17:00-16:00 CT è **un solo giorno
di trading**, il lunedì: il worst day è il singolo stop, $453 per micro, contro una DLL di Lucid
di $1.200.

**Stage 1 e "flat la sera".** Il trade attraversa la mezzanotte: nella List of Trades ingresso
la domenica, uscita il lunedì. Il controllo `--flat` di `lab.py` (nessun trade a cavallo di due
date) qui **non si applica** e non va passato: il flat che conta è "nessuna posizione dopo le
16:00 CT del lunedì", da controllare sugli orari d'uscita.

## Contaminazione

1. **Il desk ha già misurato l'IS.** Il 10/11/2026, prima di questa SPEC, su ES a 1 minuto di
   quantlake, 2020-2024, **senza stop**: versione senza filtro 257 lunedì, WR 60%, **+$29,54 per
   micro, t 2,51**; trade peggiore −$687 per micro, escursione contraria peggiore −$1.028 per
   micro. Per anno, media per trade: 2020 **+81,2**, 2021 +16,5, 2022 −0,2, 2023 +42,1, 2024
   +8,0. Sono **attese da riprodurre** in MultiCharts, non una validazione. Non sono
   confrontabili uno a uno con il nostro run:
   - **lo stop** cambia i numeri: tutte le perdite oltre i 90 punti (fra cui il trade peggiore
     senza stop, circa −137 punti) diventano −$453, e qualche trade che senza stop recuperava diventa
     una perdita piena;
   - **i festivi**: 257 sono i lunedì 2020-2024 con una sessione Globex (261 meno le 4 chiusure
     piene del CME); la nostra versione ne esclude 29 per regola NYSE e ne trada 232. La
     misura del desk include con buona probabilità i lunedì festivi, che hanno una sessione
     ridotta.
2. **Quattro varianti viste.** Il desk ha guardato su dati proxy le tre versioni con filtro
   dell'autore (L644ES con EMA, L656ES dopo un venerdì in rialzo, L644NQ con ADX) e la versione
   senza filtro. **k = 4.** Si pre-registra solo la senza filtro con lo stop. Lato autore il k è
   più alto e non si conosce: la finestra 19:00 → 15:55 è "la zona selezionata" di una ricerca
   su orari.
3. **L'OOS è visto dall'autore.** La scheda dichiara un OOS **2024-01-07 → 2026-09-21**, già
   pubblicato (tre strategie insieme, profitto concentrato nel 2025-2026). Il nostro OOS
   2025-2026 ci sta dentro: **verdetto OOS asimmetrico** (fallire conta pieno, passare vale
   come ingresso in prova). **Fuori campione pulito: dopo il 21/09/2026.**
4. **L'autore stesso** scrive che nessuna delle tre passa da sola una soglia OOS severa e le
   propone solo come aggiunta a un book, per il rischio di chiusura per inattività su un conto
   funded (un giorno di trading a settimana). Qui entra solo per la via B, come marginale.

## Rischi scritti prima

- **Il 2020 pesa troppo.** Nella misura del desk il 2020 fa da solo poco più di metà del
  profitto dell'IS (81,2 di media su ~52 trade, contro circa 16-17 di media sugli altri quattro
  anni). Se lo stop
  taglia proprio i lunedì di marzo 2020, o se senza il 2020 l'edge è quello di una moneta, la
  fase 2 può passare per un anno solo. Il criterio di via B non guarda la concentrazione annuale
  (è un criterio live, `prop_vs_live.md`); la si **stampa** e la si scrive nel verdetto, non
  uccide.
- **Gap oltre lo stop.** Domenica 15/03/2020 ES è andato limit down in Globex: con un mercato
  bloccato al limite lo stop non si riempie, e alla riapertura il fill può arrivare molto oltre i
  90 punti. Se succede, il trade peggiore supera $500 per micro e **la fase 2 è un kill**, come
  scritto sotto. Non si rigira con uno stop diverso.
- **Decadimento**: 2022 −0,2 e 2024 +8,0 nella misura del desk, 2024 "quasi piatto" nella
  scheda dell'autore. Coerente con un effetto pubblicato che si spegne.
- **Inattività**: da sola tradarebbe 4 giorni al mese. Irrilevante nel book (DPB trada tutti i
  giorni), decisivo fuori.

## Criteri per fase

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica** | periodo **dentro l'IS**: chart dal **01/02/2020 al 29/05/2020** (15 trade attesi: lunedì 3, 10, 24/02; 2, 9, 16, 23, 30/03; 6, 13, 20, 27/04; 4, 11, 18/05; esclusi 17/02 Presidents' Day e 25/05 Memorial Day). Ingressi solo alle 19:00 CT della domenica, anche il **08/03/2020** (cambio dell'ora legale: l'ingresso resta alle 19:00 CT); uscite solo per stop a −90, target a +100 o tempo alle 15:55 CT del lunedì; nessuna posizione dopo le 16:00 CT; max 1 trade per data d'ingresso; run ×10 con P&L esattamente ×10 | si corregge il codice, non è un kill |
| **2 — IS 2020-2024** | **via B**: **t > 1,03** (soglia di `lab.py` per k = 4) **e** trade peggiore ≤ **$500 per micro** | cimitero |
| **3 — OOS 2025 → oggi**, una volta | gate marginale contro il book di riferimento (`pipeline_semplice.md`, fase 3b) | cimitero, definitivo |

Lo Stage 1 è su marzo 2020 di proposito: è il periodo in cui stop e target scattano davvero, e
contiene un cambio d'ora e due festivi. Non è un'occhiata ai risultati: la SPEC è già committata.

**Via A esclusa.** La via A chiede t ≥ 2, WR ≥ 55% e R:R 0,5-1. Qui l'R:R non è una regola: con
uscita a tempo, stop a 90 e target a 100 la vincita media e la perdita media escono dal mercato, e
stare dentro o fuori dalla banda 0,5-1 (attorno a 1) sarebbe un caso, non una proprietà della
strategia. E il t ≥ 2 della via A è una soglia per k = 1: con quattro varianti già viste non
vuol dire quello che dice. Si giudica solo con la via B.

**Fase 3.** Book di riferimento: **quello in vigore in `pipeline_semplice.md` al momento del
gate**, con i report scritti lì. Oggi (10/11/2026) è **DPB 1 micro + Gold Asian Range pct1 1 +
Overnight Bias ORB 1**, tetto del book 5 strategie. MondayLong a **1 micro**. I quattro
criteri del gate tutti insieme (Δ pass rate iid ≥ +2,0 pp, Δ contiguo ≥ 0, giornata peggiore del
book ≥ −$1.200, avg trade OOS > 0). Il verdetto è asimmetrico (punto 3 della contaminazione).

## Cosa è congelato e cosa è libero

**Congelato**: ingresso 19:00 CT della domenica, uscita 15:55 CT del lunedì, stop 90 punti,
target 100 punti, calendario dei festivi per regola, nessun filtro, solo long.

**Libero**: niente che tocchi l'edge. La size la decide il gate (1 micro) e poi il simulatore.
Gli orari sono in CT: se il chart non è in timezone Exchange, sono da convertire e non da
"aggiustare".

## Varianti pre-registrate

**Nessuna.** Le tre versioni con filtro dell'autore sono già state viste (contano nel k = 4) e
non si girano. Uno stop diverso da 90, un filtro, un gemello del venerdì o del martedì, il
passaggio a NQ: ognuna è una SPEC nuova (`SPEC_<variante>.md`) con k = 5 o più, scritta prima del
run.

## Setup del chart

@ES continuo, **5 minuti**, sessione **CME Globex 17:00-16:00 CT senza pause** (non il template
RTH, non uno con la pausa delle 15:15-15:30), timezone **Exchange**, barre timbrate alla
chiusura, **Bar Magnifier 1 minuto**, IOG off. Commissione **$15 per lato** per contratto,
slippage 0. Point value $50. 1 contratto (Stage 1 anche 10). I risultati per micro sono quelli di
@ES divisi per 10.

## Pre-registrazione
- via: B            # via A esclusa: R:R non è una regola (uscita a tempo, stop 90 e target 100), e il t >= 2 vale per k = 1
- k-varianti: 4     # il desk ha visto su dati proxy le tre versioni con filtro dell'autore e la senza filtro; si registra solo la senza filtro con stop 90
- attesa: t IS in MultiCharts fra 1,5 e 2,5, WR 55-62%, 232 trade (lunedì 2020-2024 esclusi i festivi NYSE), trade peggiore -$453 per micro (lo stop) salvo un gap oltre lo stop. La misura del desk senza stop è t 2,51 su 257 lunedì festivi compresi: stop e festivi la spostano, in una direzione che non sappiamo; poco più di metà del profitto viene dal 2020, ed è il rischio principale
- kill: fase 2 t <= 1,03 (soglia di lab.py prereg per k = 4) o trade peggiore > $500 per micro, anche se per un gap; fase 3 gate marginale contro il book in vigore in pipeline_semplice.md al momento del gate (oggi DPB 1 + Gold pct1 1 + Overnight Bias ORB 1 micro, tetto 5), MondayLong a 1 micro, tutti e quattro i criteri; verdetto OOS asimmetrico, fuori campione pulito dopo il 21/09/2026
- costi: $15 per lato nel campo commissione di @ES ($30 a giro, $3 per micro), slippage incluso; slippage di MultiCharts 0
