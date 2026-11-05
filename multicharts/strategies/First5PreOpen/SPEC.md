# SPEC — First5 PreOpen, NQ (Stage 0, 05/11/2026)

**Fonte:** Carlo Zarattini e Andrew Aziz, *Can Day Trading Really Be Profitable?* (SSRN): ORB
sulla prima candela da 5 minuti su QQQ, stop all'altro estremo della candela, target 10R, flat a
fine seduta. Più il filtro di Marco Morrone (video YouTube, il link non è nel repo): la candela del
future NQ dei 5 minuti prima dell'apertura deve avere lo stesso segno della prima candela.
**Codice:** `First5PreOpen.txt`, da scrivere dopo il commit di questa SPEC.

## Ipotesi

La prima candela da 5 minuti del cash dice da che parte sta il flusso della giornata, ma da sola
è rumorosa. Se la candela del future che la precede ha lo stesso segno, la direzione era già nel
prezzo prima dell'apertura e l'apertura la conferma. Si entra in quella direzione alla fine della
prima candela, si mette lo stop all'altro estremo della candela e si tiene fino alle 15:00 CT.
Molte perdite piccole, poche giornate di trend che le pagano.

## Perché dovrebbe funzionare

Negli ultimi minuti prima delle 08:30 CT il future prezza gli sbilanci d'apertura (ordini MOO,
esecuzioni programmate, copertura delle notizie della notte). Se l'apertura va nello stesso verso,
il flusso del cash si somma a quello del future. Se va in verso opposto, la prima candela è più
spesso assestamento che direzione, e il filtro la scarta.

**Chi perde:** chi fada l'impulso d'apertura nei giorni di trend e chi prende profitto presto. I
giorni di trend sono pochi: da qui il WR basso e la coda destra.

**Avvertenza.** Il meccanismo sopra è una spiegazione scritta dopo. Il filtro è stato scelto a
posteriori (vedi Contaminazione), e non c'è una ragione strutturale misurata.

**Ruolo nel book.** La forma del P&L è l'opposto di DriftPullback: WR basso e R:R alto invece di WR
alto e R:R basso. La via è la B perché vale solo se alza il pass rate del book, non da sola.

## Cosa la rende diversa da quello che è già stato provato

| già provata | cosa ha in comune | cosa cambia qui |
|---|---|---|
| **NQ First5**, parente diretto | prima barra da 5 minuti, tenuta fino alle 15:00, long e short | **stop strutturale** all'altro estremo della candela, che rende il rischio per trade noto in anticipo: era il motivo per cui l'altra non entrava nel conto. **Il segno della barra pre-open** sostituisce la EMA come seconda condizione. Ingresso `next bar at market` invece di `this bar at close`. Non è una variante di parametro: cambiano la condizione d'ingresso e la struttura del rischio, per questo ha cartella e SPEC sue |
| **ORB NQ** | apertura, NQ | range di 5 minuti invece di 30, long e short invece di solo long, ingresso a mercato sulla chiusura della candela invece che sulla rottura del range. Non c'è un breakout da aspettare |
| **Overnight Bias ORB** | stessa famiglia, stessa ora, stesso strumento | il bias viene dal segno di una barra sola e non dalla posizione dell'open nel range della notte; niente ADX, niente filtro sul range, niente target. **La correlazione col book va guardata al gate**: è il rischio principale di questa candidata |
| **DriftPullback** (live) | NQ intraday, momentum | un trade al giorno all'apertura contro fino a quattro nella seduta, forma del P&L opposta. Anche questa è una correlazione da misurare al gate, non da assumere |

## Regole

| | |
|---|---|
| Famiglia | opening range / momentum d'apertura, long e short |
| Strumento · TF · sessione | @NQ → MNQ · **5 min** · Globex 17:00–16:00 CT senza pause, timezone Exchange (CT), Bar Magnifier 1 min. MC timbra la barra alla chiusura |
| Barra pre-open | `Time = 830` (08:25–08:30). Segno = `Close − Open` |
| Prima candela | `Time = 835` (08:30–08:35). Segno = `Close − Open` |
| Armamento | sulla barra 835, con la barra precedente che ha `Time = 830` e la stessa `Date`. Una barra mancante vuol dire niente trade |
| Trigger | segni entrambi positivi → **long**; entrambi negativi → **short**; discordi, o una delle due con corpo nullo → **niente trade**. Con `PreOpenFilter 0` conta solo il segno della prima candela |
| Ingresso | `next bar at market`, cioè all'apertura delle 08:35. In List of Trades il timbro è **08:40** |
| Stop | long: `Low` della prima candela; short: `High`. **Al livello**, senza buffer, attivo dalla barra d'ingresso (vedi sotto) |
| Target | nessuno. `TP_RR 0`; il 10R del paper non scatta quasi mai e non è nella versione pre-registrata |
| Uscita a tempo | prima barra con `Time ≥ 1500` → `next bar at market` (prezzo delle 15:00, timbro 15:05). `SetExitOnClose` come rete |
| Guardrail | un trade al giorno, per costruzione: c'è una sola barra di segnale e nessun rientro dopo lo stop. Solo lunedì–venerdì. **Nessun tetto alla distanza dello stop**: non era nella regola e non si aggiunge dopo aver visto l'IS |
| Trade/giorno | 0 o 1, circa un giorno su due |
| Profilo atteso | WR ~25%, R:R realizzato intorno a 3,5–4 (dedotto, vedi Conti). Fuori dalla via A per costruzione |

**IS**: 2020-01-01 → 2024-12-31 · **OOS**: 2025-01-01 → oggi.

### Input

`PreOpenFilter(1)` (0 = solo prima candela) · `TP_RR(0)` · `NumContracts(1)` · `ShowLog(0)` ·
`TradeStartEL(0)` · `TradeEndEL(0)`.

Gli orari 830, 835 e 1500 sono costanti nel codice: fanno parte della regola.

`TradeStartEL` / `TradeEndEL` non servono per il lead-in, perché la strategia non ha indicatori e
non ha riscaldamento. Si tengono per un altro motivo: sul run IS `TradeEndEL 1241231` impedisce di
aprire trade nell'OOS anche se il chart ha più dati del previsto. Agiscono solo sugli ingressi.

### Lo stop: ordine a prezzo, non ordine speciale

La regola dice «a quel livello». Le due strade che abbiamo nel repo non danno la stessa cosa.

| | `SetStopLoss` (come BTC_First30) | **ordine stop a prezzo (come Overnight Bias)** |
|---|---|---|
| barra d'ingresso | coperta | coperta: l'ordine `-SL0` parte sulla barra del segnale, insieme all'ingresso |
| dove sta lo stop | `fill − distanza`: la distanza si misura dal fill, che sul segnale non si conosce ancora. Lo stop si sposta dello scarto fra close delle 08:35 e open della barra dopo | **sul livello esatto**, qualunque sia il fill |
| contratti | importo per posizione: va moltiplicato per `NumContracts` | prezzo: scala da solo |
| già verificato | sì | sì, Stage 1 di Overnight Bias: `OBO-L-SL0` e `OBO-S-SL0` scattati sulla barra d'ingresso |

**Scelta: ordine stop a prezzo.** Sulla barra 835, insieme all'ingresso,
`Sell ("F5P-L-SL0") next bar at stopPx stop` (mirror `BuyToCover ("F5P-S-SL0")` per lo short); poi,
a ogni barra in posizione, lo stesso ordine a prezzo `F5P-L-SL` / `F5P-S-SL`, finché non scatta
l'uscita a tempo. `stopPx` si fissa sul segnale e non si muove.

Motivi: è la regola scritta e non una sua approssimazione, e toglie di mezzo la trappola del
per-posizione × contratti.

**Caso limite.** Se l'apertura delle 08:35 fosse già oltre il livello, lo stop scatta subito e il
trade chiude nella barra d'ingresso. Su una serie continua senza pause alle 08:35 non ce lo
aspettiamo; se capita si vede nella lista trade e resta com'è.

**Target, se mai acceso.** Con `TP_RR > 0`: ordine limit a prezzo, `Close ± TP_RR × |Close − stopPx|`
dalla close del segnale, stesso schema dello stop. Serve solo per i controlli di meccanica.

**Dal vivo, se ci arriva.** Vale il punto aperto di `go_live.md` su Overnight Bias: va controllato
nella scheda Orders che lo stop compaia subito dopo il fill. Non cambia il backtest.

### Giornate corte e calendario

Niente calendario nel codice: si tradano tutti i giorni in cui le barre 830 e 835 esistono.

| giorno | cosa succede |
|---|---|
| **Mezza giornata col cash aperto** (venerdì dopo il Ringraziamento, vigilie) | il segnale vale; l'uscita è `SetExitOnClose` sull'ultima barra, intorno alle 12:00 CT. Stesso comportamento già visto su NQ First5 |
| **Festivo USA col Globex aperto fino alle 12:00 CT** (MLK, Presidents, Memorial, Juneteenth, 4 luglio, Labor, Ringraziamento) | le barre 830 e 835 esistono, ma **alle 08:30 non apre nessun cash** e l'ipotesi non vale. Il codice non lo sa e tratta il giorno come gli altri, uscita come sopra. Sono circa 7 giorni l'anno, quindi 3–4 trade su ~124. Lasciarli dentro è la scelta più semplice: una lista di date sarebbe un'altra decisione presa con l'IS già guardato. In fase 1 si annotano |
| **Giorno senza barre** (Venerdì Santo, Natale, Capodanno) | niente barra 830 o 835, niente trade |
| **`SetExitOnClose` non scatta** | la prima barra con `Time ≥ 1500` diventa quella della sera, e il trade esce dopo le 17:00. Non è previsto: se compare in fase 1 è un bug |

## Conti

NQ = $20/pt, MNQ = $2/pt. Costo $15 a giro per NQ, $1,50 per micro.

| | NQ mini | MNQ micro |
|---|---|---|
| Stop tipico: **35–50 pt, stima** | $700–1.000 | $70–100 |
| Target | nessuno | nessuno |
| Trade peggiore nel proxy | $2.730 | $273 |
| Soglia di kill sul trade peggiore | **$5.000** | **$500** |
| **Worst day** | = trade peggiore | = trade peggiore |

- **Lo stop non è fisso.** È la distanza fra il fill e l'altro estremo della prima candela, e cresce
  con la volatilità d'apertura.
- **La stima 35–50 pt non è una misura.** È dedotta dai numeri del proxy: avg $193, t 2,40 e 621
  trade danno uno scarto tipo di ~$2.000 per NQ; con WR 24,6% e vincite tutte uguali la perdita
  media sarebbe ~$950 (~48 pt) e la vincita ~$3.700, cioè R:R ~3,9. Con vincite disperse, come qui,
  la perdita media è più bassa. Si misura in fase 1 e in fase 2.
- **Worst day = worst trade**, perché il trade è uno solo. Sono possibili stop peggiori del livello
  se il prezzo salta: lo slippage sugli stop è il motivo per cui l'attesa in MC è sotto il proxy.
- **Il rischio vero è la serie perdente, non il trade.** Con WR 25% in 620 trade la serie più lunga
  attesa è di ~18 perdite di fila, cioè circa 7 settimane e ~$1.500 per micro. È aritmetica, non
  misura, e sta già vicino all'MLL di Lucid. Lo giudica il gate marginale.

## Contaminazione

1. **L'IS 2020–2024 è già stato guardato**, dal desk, il 05/11/2026, su NQ a 1 minuto di quantlake.
   È una misura proxy in Python, non MultiCharts. Il filtro non è quindi scelto alla cieca. Risultato
   del proxy sull'IS: **621 trade, WR 24,6%, avg +$193 per NQ dopo $15 a giro, t 2,40, trade peggiore
   $273 per micro, cinque anni su cinque positivi, long e short positivi.** Sono le attese da
   riprodurre in MC, **non un risultato di validazione**.
2. **Cinque versioni provate sul proxy** per arrivare a questa: senza stop; stop; stop + target 10R;
   stop + target 1R; stop + filtro pre-open. Quindi k = 5. La versione pre-registrata è **solo
   l'ultima**: stop e filtro pre-open, senza target.
3. **L'OOS 2025–2026 non è stato guardato da nessuno di noi.** Si gira una volta sola.
4. **Il filtro è stato scelto da Morrone a posteriori**, su QQQ, 2016–2023 circa. Il nostro IS ci si
   sovrappone in gran parte: la sua tenuta sul 2020–2023 non è una conferma indipendente. Il solo dato
   fuori dalla sua selezione e dalla nostra è l'OOS, per la parte successiva al suo periodo.
5. **Differenze dalla fonte.** NQ al posto di QQQ per entrambe le candele; size fissa invece del
   rischio in percentuale del paper; niente target. Il flat alle 15:00 CT è la chiusura del cash,
   come nel paper.

## Cosa è congelato e cosa è libero

**Congelato:** gli orari 830, 835 e 1500; la regola dei segni; lo stop al livello senza buffer;
`PreOpenFilter 1`; `TP_RR 0`; niente calendario; niente tetto allo stop.

**Libero:** `NumContracts` (solo per il test ×10), `ShowLog`, `TradeStartEL` / `TradeEndEL`.

## Varianti pre-registrate

**Nessuna.** `PreOpenFilter 0` e `TP_RR > 0` esistono nel codice solo per i controlli di meccanica
della fase 1. Un run IS con quei valori è una variante nuova: SPEC propria e k = 6, non un confronto
a margine. Niente Stage 4 su questa strategia.

## Criteri

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica**, 2024-08-01 → 2024-12-31 | ingressi solo all'apertura delle 08:35 (timbro 08:40); verso uguale al segno delle due barre e nessun trade nei giorni discordi (controllo su 5 giorni per tipo dal log); stop esattamente sul `Low` / `High` della prima candela (5 trade a mano); `-SL0` che scatta anche sulla barra d'ingresso; flat a 15:00 o sull'ultima barra nelle giornate corte; max 1 trade al giorno; test ×10 esatto | si corregge il codice |
| **2 — IS 2020–2024** | **solo via B**: **t > soglia k** (1,16 con k = 5, da `lab.py prereg`) e trade peggiore ≤ $500 per micro ($5.000 nel report). WR e R:R della via A esclusi per costruzione | cimitero |
| **3 — OOS 2025–2026**, una volta | i quattro criteri del gate marginale di `pipeline_semplice.md`, candidata a 1 micro, contro il book di riferimento in vigore in quel momento | cimitero, definitivo |

**La fase 1 sta nell'IS, non negli ultimi 100 giorni.** Gli ultimi 100 giorni sono dentro l'OOS, che
non deve vedere nessuno prima della fase 3. Il periodo scelto copre circa 105 sedute, con due mezze
giornate (29/11 e 24/12/2024) e tre festivi (Labor Day, Ringraziamento, Natale).

**Se MC e proxy divergono.** Con n fuori da 550–680 o WR fuori da 22–27% si cerca la causa (dati,
festivi, codice) prima di leggere il t. Non è un kill: il kill è quello scritto nella tabella.

**Attesa OOS.** Il caso base è l'edge dimezzato. Con ~230 trade vuol dire un t OOS intorno a 0,6–0,7,
e una probabilità non piccola di avg negativo per solo rumore. Il criterio 4 del gate (avg OOS > 0)
può quindi uccidere una strategia viva. Lo accettiamo: l'OOS non si rigira.

**Costi.** $7,50 per lato nel campo commissione (slippage incluso), slippage 0. Gli stop sono ordini
stop e riempiono al livello, o peggio se il prezzo salta oltre.

## Setup del chart

@NQ **5 min**, sessione **Globex** (17:00–16:00 CT, senza pause), timezone **Exchange (CT)**, Bar
Magnifier 1 min, IOG off, commissione `7.5$ per Contract`, slippage 0, 1 contratto. Niente lead-in.
Finestra con `TradeStartEL` / `TradeEndEL`: IS `1200101`–`1241231`.

**Attenzioni.**
- **Fuso orario.** Su un chart che non è in CT le barre 830 e 835 esistono lo stesso e la strategia
  trada un'ora sbagliata senza dare errori.
- **Serie back-adjusted.** La strategia usa solo differenze dentro la giornata: la traslazione di
  `@NQ` non la tocca, e la posizione non attraversa mai un rollover.

## Pre-registrazione
- via: B            # WR ~25% e R:R alto: fuori dalla via A per costruzione
- k-varianti: 5     # cinque versioni sul proxy: senza stop; stop; stop+target 10R; stop+target 1R; stop+filtro pre-open. Pre-registrata solo l'ultima
- attesa: IS in MultiCharts t fra 1,5 e 2,4 (slippage sugli stop e fill peggiori del proxy, che ha dato t 2,40), WR 22-27%, ~600 trade, trade peggiore sotto $500 per micro. OOS: edge dimezzato è il caso base
- kill: fase 2 via B t <= soglia k di lab.py prereg (1,16 con k = 5) o trade peggiore > $500 per micro; fase 3 gate marginale contro il book di riferimento di pipeline_semplice.md
- costi: $7,50 per lato nel campo commissione (slippage incluso), slippage 0
