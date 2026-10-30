# SPEC — DriftPullback v2.1 (Stage 0)

**Ipotesi**: quando il Nasdaq ha già driftato in una direzione durante la seduta, quel
drift tende a continuare; il posto più economico per entrarci non è il breakout ma il
**primo pullback contro** il drift.
**Perché**: letteratura sul momentum intraday dei futures su indice (famiglia "fast
alpha", Zarattini & Pagani). I trend intraday sono alimentati da flussi che non si
esauriscono in una stampata sola — ribilanciamenti sistematici, hedging di book di
opzioni, momentum chaser che arrivano tardi. Un pullback poco profondo dentro un drift
già stabilito è quasi sempre una pausa (presa di profitto, caccia agli stop), non
un'inversione.
**Chi perde**: chi fade la prima discesa e chi insegue tardi pagando lo spread al
momentum. Noi forniamo liquidità di continuazione a un prezzo un po' migliore.
**Fonte**: tutorial completo di Francesco Agnello
(`mc/education/protocollo/11. Strategy Feedbacks/1. DriftPullback_Tutorial_.pdf`, 18 pp.,
riporta ogni blocco del sorgente v2.1) + live 002 del corso. **Il sorgente non è nel
repo**: il codice in `DriftPullback.txt` è una riscrittura dal walkthrough del PDF →
lo Stage 1 è una verifica di *fedeltà*, non solo di meccanica.
**Stato dichiarato dall'autore**: validato, in live su conti funded. Per noi resta un
candidato da rivalidare: i suoi numeri non sono i nostri.

**Ruolo nel basket**: è **l'unica candidata del corso che nasce già col profilo prop**
invece di doverci essere adattata — WR alto, R:R 0.5, flat EOD, e soprattutto un **cap
strutturale di perdita giornaliera** scritto nella strategia (`MaxLossesPerDay 2`).
Porta anche il lato **short**, che oltre a NQ First5 manca al basket.

| | |
|---|---|
| Famiglia | momentum intraday / continuazione del drift, long e short |
| Strumento · TF · sessione | @NQ · **due serie: data1 = 5 min (esecuzione), data2 = 15 min (segnale)** · Globex 24h, chart CT |
| Armamento (15m, solo a fine barra) | close oltre l'ancora **e** ancora inclinata nella stessa direzione **e** drift 1h ≥ ±0.10% |
| Ancora | `AnchorType` 2 = VWAP di sessione (default v2.1) · 0 = SMA(20) — **entrambe validate dall'autore** |
| Trigger (5m) | prima barra contro il drift (rossa se long, verde se short) entro **6** barre 5m dall'armamento → *next bar at market* |
| Exit | bracket fisso: stop **80 pt**, target **40 pt** long / **50 pt** short; flat a 14:55 CT; `SetExitOnClose` |
| Guardrail | max **4** ingressi e max **2** perdite al giorno |
| Trade/giorno | 1–4 |
| Profilo dichiarato | avg $77, WR 65%, t-stat OOS 2.2 |

**IS**: 2020-01-01 → 2024-12-31 · **OOS**: 2025-01-01 → oggi.
Configurazione di riferimento = quella validata: `AnchorType 2`, `ExitMode 0`,
`SizeMode 1`, `BaseCts 1`, `StopSlipTicks 2`, tutti i default di sessione su chart CT.

## Perché il bracket è "al contrario" (ed è il punto)

Stop largo 80 pt, target piccolo 40–50: sembra rovesciato finché non lo si lega al
meccanismo. I pullback dentro un drift si risolvono **poco profondi e in fretta**, quindi
la strategia compra un win rate alto su un tragitto corto e lo paga con stop pieni
occasionali. È il motivo per cui i guardrail giornalieri non sono decorazione: servono a
limitare quanti di quegli stop può consegnare una giornata storta.

**Conti (1 contratto, NQ = $20/pt; ÷10 = equivalente micro MNQ)**

| | NQ mini | MNQ micro |
|---|---|---|
| Stop 80 pt + 2 tick di slippage | $1.610 | $161 |
| Target long 40 pt | $800 | $80 |
| Target short 50 pt | $1.000 | $100 |
| **Worst day** (2 stop) | **$3.220** | **$322** |

Su Apex 50k (daily loss $1.000) il worst day struttrale consente **fino a 3 micro**
(3 × $322 = $966). È il primo caso in cui il numero di contratti massimo non lo decide il
simulatore Monte Carlo ma la strategia stessa — e il simulatore dello Stage 7 non potrà
che confermarlo o abbassarlo.

## Cosa è congelato e cosa si può toccare

**Congelato** (ri-ottimizzarlo non migliora la strategia, cancella la validazione):
`DriftThreshPct 0.10` (è una *definizione di regime*, non un parametro), `MALen 20`,
`DriftLen 4`, `PullbackWindow 6`, i bracket 80/40/50, `StopSlipTicks 2`.

**Libero**: gli orari (per far combaciare il fuso del chart), i toggle di lato,
`AnchorType` / `ExitMode` per gli esperimenti, il sizing (per far combaciare il conto).

## Varianti pre-registrate (Stage 4)

1. **`AnchorType` 0 (SMA) vs 2 (VWAP di sessione)** — A/B legittimo, non ottimizzazione:
   sono due ancore entrambe validate dall'autore sullo stesso identico modello temporale.
   La VWAP ha il "perché" più forte (è il prezzo su cui il resto del mercato è
   benchmarkato). Split-sample come per ogni filtro.
2. **Solo short** (`TradeLongs 0`) — il lato che manca al basket va misurato anche da solo.
3. **`ExitMode 1`** (stop/target in multipli di ATR congelati all'ingresso) — **bassa
   priorità**: l'autore dichiara di averla testata formalmente contro i bracket fissi e
   di averla scartata; i moltiplicatori spediti sono *seed*, non valori validati.
4. **`MaxLossesPerDay` 1** — variante prop pura: dimezza il worst day a $161/micro e
   permette di raddoppiare la size. Da verificare che non tagli via i recuperi di giornata.
5. **`EntryMode` 1 — ingresso su stop** 1 tick oltre l'estremo della barra di pullback,
   invece che *next bar at market*: setup armato, barra contraria → buy‑stop sopra il
   massimo di quella barra (mirror per gli short), valido `EntryStopBars` barre, livello
   fisso che non insegue. Il drift deve **riprendere** prima che si sia dentro, quindi
   filtra i pullback che proseguono. Idea dal Triple Screen di Elder (1993), stessa
   architettura dual‑timeframe di questa strategia — vedi `mc/education/books/NOTES_elder.md`.
   Costo noto da misurare, non da assumere: si perdono i trade in cui il rimbalzo riparte
   subito senza superare quel massimo, e i fill sono per definizione a un prezzo peggiore
   della chiusura del pullback.
   **Non** risolve la barra d'ingresso scoperta: rende noto in anticipo il *prezzo*
   d'ingresso, ma il bracket resta un ordine next‑bar emesso dalla posizione, esattamente
   come in `EntryMode` 0.
   Confronto da fare come A/B nello stesso run (`EntryMode` 0 vs 1), split‑sample sulle due
   metà dell'IS; `EntryStopBars` 1 è il default, 2–3 solo se l'A/B è promettente e sempre
   come cluster, mai come picco.
6. **`TriggerMode` 1 — barra di pullback con rifiuto.** Il trigger validato è molto grezzo:
   una candela sola, solo il segno di `Close − Open`. La variante chiede in più che la
   chiusura sia lontana almeno `RejShadowFrac` (0.5) del range dall'estremo del pullback —
   cioè che il movimento contrario sia stato **rifiutato dentro la barra** invece di essere
   solo una pausa. Meccanismo dichiarabile, un parametro, misurato con la posizione della
   chiusura nel range (robusta, niente definizioni di ombre e corpi da inventare).
   Spunto da Palmquist, *Money‑Making Candlestick Patterns* — vedi
   `mc/education/books/NOTES_palmquist_candlestick.md`: è anche l'unico uso dei pattern
   che quel libro sostiene, timing dentro un contesto e mai strategia autonoma.
   Atteso: meno trade e WR più alto. Se il WR non sale, la variante non serve — e con un
   R:R 0.5 perdere trade senza guadagnare win rate peggiora tutto.
   Compone con `EntryMode`: le due si testano prima da sole, poi insieme.

`SizeMode 2` (cushion ladder: +1 contratto ogni $2.000 di profitto bancato, tetto 3) **non
è una variante di edge**: è logica di deployment, si valuta allo **Stage 7**, non prima.
Fino ad allora tutti i run sono a size fissa, 1 contratto.

## Kill

Gate della pipeline. In più, kill specifici:
- avg trade netto IS < $70 — il valore dichiarato è $77, il margine sul nostro gate è
  sottile: **con costi realistici questa è la metrica che la uccide per prima**;
- WR < 55% — è l'intera tesi della strategia: senza win rate alto un R:R 0.5 è una
  macchina per perdere;
- se la riscrittura non riproduce il comportamento descritto nel PDF (Stage 1), la
  strategia non entra nello Stage 2: si corregge il codice o si chiude.

## Attenzioni specifiche

- **Fuso orario.** I cinque input di sessione sono in ora del chart e non c'è nessun
  errore se sono sbagliati: si tradano semplicemente ore diverse da quelle validate. I
  default sono CT. Tabella di conversione in `README_DPB.md`.
- **Barra d'ingresso scoperta.** I bracket sono ordini *next bar* emessi dalla posizione:
  la barra d'ingresso corre senza stop né target. È una conseguenza del modello a ordini
  next-bar, non un bug — ma il rischio reale su un trade è 80 pt **più** l'escursione
  della barra d'ingresso.
- **Correlazione.** Sarebbe la quinta strategia su NQ e la terza di famiglia momentum
  (ORB, VaultBreak, First5). Il gate 8 vuole correlazione ~0. Misurarla con ORB e First5
  **subito dopo lo Stage 2**, non allo Stage 8: se è alta, nel basket ne entra una sola.
- **Regime.** Nelle live 004 e 005 l'autore la mette in panchina perché in drawdown
  severo rispetto allo storico. Non è un difetto della strategia — è esattamente il
  comportamento codificato nel nostro gate 8 (bench sopra il 90° percentile MC, rientro
  solo a nuovo massimo di equity) — ma significa che il regime recente le è ostile, e
  che l'OOS 2025+ va guardato con quell'aspettativa.

## Attenzione dati — serie back‑adjusted (29/09/2026)

`@NQ` di TradeStation è un **contratto continuo back‑adjusted**: il presente è corretto, il
passato è traslato dell'aggiustamento accumulato sui rollover. Riscontro: il 03/01/2016 la
serie segna ~8.440 mentre il NQ vero stava intorno a 4.500, cioè ~3.900 punti di scarto.

**Per le altre cinque strategie è irrilevante**: lavorano su *differenze* di prezzo (range
ORB, ATR, stop e target in punti, distanze dal VWAP), e una traslazione costante non le tocca.

**Per DriftPullback no**, ed è l'unica:

```
driftPct = (Close of data2 - Close[DriftLen] of data2) / Close[DriftLen] of data2 * 100
```

È una **percentuale del prezzo**. Su una serie traslata la stessa escursione in punti dà
una percentuale diversa a seconda dell'anno: nel 2016, 40 punti erano lo 0,88% del prezzo
vero (4.530) ma risultano lo 0,47% su quello aggiustato (8.440). La soglia
`DriftThreshPct 0.10` — che il tutorial chiama esplicitamente *una definizione di regime,
non un parametro da ottimizzare* — misurerebbe quindi regimi via via più permissivi
andando indietro nel tempo, e l'IS 2020–2024 sarebbe misurato con un metro diverso
dall'OOS.

**Da risolvere prima dello Stage 1**, in quest'ordine:
1. **Serie non back‑adjusted** per questa strategia (il tipo di contratto continuo è
   configurabile lato simbolo). È la soluzione da provare per prima perché non tocca il
   codice e lascia i parametri congelati come sono.
2. Solo se la 1 non è praticabile: riscrivere il drift in **punti normalizzati per ATR**
   invece che in percentuale. Più invasiva — cambia una definizione congelata dall'autore,
   quindi i suoi numeri di riferimento non sarebbero più confrontabili.

Non accettare la terza via (usare la serie aggiustata e tirare avanti): renderebbe l'unico
parametro non ottimizzabile della strategia dipendente dall'anno.

---

# Aggiornamento 15/10/2026 — tre cose cambiate, e una contraddizione nei numeri dichiarati

## 1. Il sorgente originale è arrivato

Sopra è scritto «**Il sorgente non è nel repo**: il codice in `DriftPullback.txt` è una
riscrittura dal walkthrough del PDF → lo Stage 1 è una verifica di *fedeltà*». **Non è più
vero.** Il materiale del protocollo del 13/10 contiene la v2.1 dell'autore in
`education/protocollo/9.TheBridge/STRATEGIES/PROP FIRM NATIVE LOW RR/Drift Pullback.txt`.

Lo Stage 1 torna quindi a essere una verifica di **meccanica** e non di fedeltà. Si usa il
sorgente dell'autore, non la nostra riscrittura.

Dalla v2.1 si impara anche che `SizeMode 1` (default) è a **lotto fisso**: solo `SizeMode 2`
compone sul cushion. **Mai usare 2.**

## 2. Il blocco resta, e la via di sblocco è una riga

Il drift è ancora `(Close − Close[n]) / Close[n] × 100` sul prezzo grezzo, e il commento del
codice dell'autore lo dichiara esplicitamente («*on the raw 15m close, UNCHANGED*»). Su un
continuous back‑adjusted è inaffidabile, e adesso abbiamo la conferma indipendente dalla
misura su @GC: il 2020 mostrava un prezzo medio d'ingresso di 2.459 quando l'oro reale stava
fra $1.500 e $2.070.

**Sblocco pre‑registrato**: drift in unità di ATR invece che in percentuale,
`(Close − Close[n]) / AvgTrueRange(14)`. Una riga.

## 3. Lo stop dichiarato è sopra il budget

`LongSLpts 80` su @NQ vale **$160 per micro**, contro un budget di **$60–110** imposto dai
gate sul drawdown. Con gli ATR ora misurati (NQ 210 punti, YM 339):

| | punti | $/micro | in ATR |
|---|---|---|---|
| dichiarato, MNQ | 80 | **$160** | 0,38 |
| a budget, MNQ | 55 | $110 | **0,26** — dentro il rumore |
| a budget, MYM | 220 | $110 | **0,65** |

Su MNQ, per stare nel budget, lo stop finisce dentro il rumore. **Su MYM lo stesso budget dà
0,65 ATR.** Il porting è una variante da pre‑registrare, non una decisione da prendere dopo
aver visto i risultati.

## 4. La contraddizione da risolvere, scritta prima del run

Il profilo dichiarato dall'autore è **avg $77, WR 65%, t‑stat OOS 2,2**. Con `LongSLpts 80` e
`LongTPpts 40` il R:R dichiarato è **0,50**, e a R:R 0,50 il «null» (probabilità di toccare il
target prima dello stop in un random walk senza drift) è **66,7%**.

**Un WR del 65% a R:R 0,50 sta SOTTO il null.** L'edge in unità di R sarebbe
E = 0,65 × 0,50 − 0,35 = **−0,025**, e il PF 0,93: in perdita. Questo **contraddice** l'avg
trade di $77 dichiarato dall'autore.

La spiegazione più probabile non è che l'autore sbagli: è che il **R:R realizzato sia più alto
di quello dichiarato**, perché l'uscita a tempo e `MaxLossesPerDay` producono perdite
*parziali*. Lo abbiamo già visto misurato su VaultBreak, dove lo stop dichiarato era 100
punti e la perdita media realizzata **60,6**.

**Conseguenza di metodo, che vale per tutte le candidate future**: con un'uscita a tempo, il
R:R dichiarato **non** è il R:R realizzato, e la formula di fattibilità va alimentata con
vincita media e perdita media **misurate**, non con i TP/SL della spec.

E una cautela su quanto avevo scritto sulla via «abbassare DD_R»: le uscite parziali alzano
il R:R realizzato **e** alzano la dispersione del P&L, quindi alzano anche DD_R. Le due cose
si muovono insieme, quindi ridurre DD_R togliendo uscite parziali **non è gratis**: costa
R:R realizzato. L'avevo presentata come la via che «non richiede più edge»: è più onesto dire
che è un compromesso, e che il saldo va misurato.

## Che cosa fare, nell'ordine

1. Sostituire `DriftPullback.txt` con il sorgente v2.1 dell'autore (verifica di meccanica,
   non più di fedeltà).
2. Applicare la riga di sblocco: drift in ATR.
3. Stage 1 su ~100 giorni, 1 contratto, `ShowLog` attivo, `SizeMode 1`. Misurare
   **vincita media, perdita media, DD_R realizzati** — non assumerli dai TP/SL.
4. Solo allora decidere strumento e budget, con la formula di fattibilità alimentata da
   numeri misurati.

---

# Stage 1 — il file e il run (15/10/2026)

File: **`DriftPullback_v21.txt`** = il sorgente **v2.1 dell'autore**, byte per byte, più
quattro aggiunte nostre, tutte marcate `NOSTRO` nel codice:

| Aggiunta | Cosa fa |
|---|---|
| `DriftMode` (0/1) | **0 = drift in % dell'autore** (originale, intatto) · 1 = drift in unità di ATR |
| `DriftThreshAtr` · `DriftAtrLen` | la soglia per il modo 1, e la lunghezza dell'ATR su data2 |
| `driftLongOK` / `driftShortOK` | booleani che sostituiscono il confronto diretto nel blocco di arming, così **la logica dell'autore non è toccata**: cambia solo quale misura la alimenta |
| log `DPB` su file | una riga per barra 15m con ancora valida, con **entrambe** le misure del drift |

`DriftPullback.txt` (la nostra vecchia riscrittura dal PDF) resta in repo come riferimento
ma **non si usa più**.

## Perché il run si lancia con `DriftMode 0`

Con `DriftMode 0` il codice è quello dell'autore. Quindi un solo run dà **tre cose insieme**:

1. **verifica di meccanica** sul codice vero (non più di fedeltà: il sorgente è l'originale);
2. **vincita media, perdita media, DD_R realizzati** — i numeri che servono alla formula di
   fattibilità, e che **non** si possono dedurre dai `LongSLpts`/`LongTPpts` dichiarati;
3. la **distribuzione congiunta di `dPct` e `dAtr`**, con cui `DriftThreshAtr` si **misura**
   invece di indovinarla.

Il default `DriftThreshAtr 0.60` è un segnaposto. **Non si usa** prima della calibrazione: è
scritto qui perché un numero vuoto in un input è peggio di un numero dichiarato provvisorio.

## Il run

| | |
|---|---|
| Chart | **Data1 = @NQ 5 min**, **Data2 = @NQ 15 min** (Insert → Series, stesso simbolo) |
| Sessione | Globex 24h, timezone **Exchange (CT)** |
| Finestra | ~100 giorni |
| `DriftMode` | **0** |
| `ShowLog` | **1** · `LogPath` `C:\mc_out\dpb_drift.txt` · `ResetFile` **1** |
| `SizeMode` | **1** (lotto fisso) · `BaseCts` **1** — **mai `SizeMode 2`**, che compone sul cushion |
| `ExitMode` | **0** (punti fissi, la configurazione validata dall'autore) |
| Costi | $7,50 per contratto |
| Bar Magnifier | 1 min se disponibile |

Creare `C:\mc_out` prima di lanciare.

## Attenzione all'orario, che l'autore segnala in maiuscolo

I cinque input di sessione sono in **ora del chart**, e i default sono per un chart **CT**:
`SessStart 930`, `SessEnd 1430`, `FlatTime 1455`, `VwapStart 0830`, `VwapEnd 1500`.
Su un chart in ora **Eastern** andrebbero `1030 / 1530 / 1555 / 0930 / 1600`. Niente dà
errore se si sbaglia: si opera semplicemente **un'ora diversa** da quella validata.

## La contraddizione da risolvere, ripetuta qui perché è il punto del run

Dichiarato: **avg $77, WR 65%**, con `LongSLpts 80` / `LongTPpts 40` → R:R dichiarato **0,50**.
A R:R 0,50 il null è **66,7%**, quindi un WR del 65% darebbe E = **−0,025** e PF **0,93**.

Se il run conferma WR ~65% **e** R:R realizzato ~0,50, la strategia è in perdita e la
contraddizione è nei numeri dell'autore. Se invece il R:R realizzato è più alto (perdite
parziali da uscita a tempo, come su VaultBreak: stop dichiarato 100 punti, perdita media
realizzata 60,6), allora il profilo torna coerente e si misura sul serio.

**Questa è la domanda del run.** Non «funziona?», ma «quali sono i numeri realizzati?».

## Risultato dello Stage 1 (15/10/2026) — la domanda è risolta, e il verdetto è sospeso

317 trade su 97 giorni (2026‑05‑29 → 10‑14), `DriftMode 0`, 1 contratto, $7,50/contratto.
Report `reports/DPB_S1_100gg_mode0.xlsx`, log `DPB_S1_drift_log.txt`.

### Meccanica

0/317 overnight · massimo 4 trade al giorno = `MaxTradesPerDay` · uscite tutte con i nomi
previsti (`L.TP` 115, `S.TP` 82, `L.SL` 55, `S.SL` 48, `L.Flat` 6, `S.Flat` 10, EOD 1) ·
long 176 / short 141. **Manca il test ×10**, che va fatto per chiudere il Gate 1.

### I numeri realizzati contro quelli dichiarati

| | dichiarato | misurato |
|---|---|---|
| WR | 65% | **64,4%** |
| R:R | 0,50 (da 40/80) | **0,596** |
| avg trade | $77 | **$42** |
| perdita media | 80 pt = $160/micro | 77,9 pt = **$156/micro** |

**La contraddizione è risolta e l'autore è onesto sul WR.** Il R:R realizzato è più alto del
dichiarato perché 16 trade escono con `Flat` prima dello stop pieno — esattamente il
meccanismo già misurato su VaultBreak. **Conferma la regola**: con un'uscita a tempo, il R:R
dichiarato non è quello realizzato.

### Il criterio di fattibilità, su questi numeri

null a R:R 0,596 = 62,7% · WR 64,4% → **eccesso +1,7 pp** (serve +5,6…+6,5)
**E = 0,0366** (serve ≥ 0,115) · DD_R = 24,5 · **RATIO = 0,33**

### Perché il verdetto è sospeso e non è un kill

Questo run è su **100 giorni del 2026**, dove l'ATR di NQ misura **367 punti** contro i
**210** del 2020‑2024: un regime **1,75×**. Lo stop è **fisso a 80 punti**, quindi:

| | 80 punti valgono | effetto atteso sul WR |
|---|---|---|
| 2026 (questo run) | **0,22 ATR** | stop dentro il rumore → WR **depresso** |
| 2020‑2024 (l'IS) | **0,38 ATR** | stop con spazio → WR **più alto** |

È l'immagine speculare di Gold Asian Range: là il 2026 lusingava la strategia, qui la
penalizza. E è esattamente il caso per cui dopo Gold abbiamo scritto che **i numeri economici
di un campione recente non anticipano il Gate 2**. Applicare qui un kill sarebbe lo stesso
errore, al contrario.

### Lo sblocco in ATR: il blocco è peggiore del previsto, ma il modo 1 non è una strategia nuova

Dal log, la soglia `DriftThreshPct 0.10` tradotta in unità di ATR **oscilla fra 0,29 e 1,06
anche dentro questi soli 100 giorni** — un fattore **3,6** — perché dipende da `atr2`, che
varia molto più del prezzo. Il drift in percentuale è quindi una soglia **inversa alla
volatilità**: arma più facilmente quando il mercato è agitato. Il blocco è reale e più grave
di come era descritto.

Ma alla soglia equivalente (**0,56 ATR**, la mediana dell'equivalente misurato) i due modi
armano 1.705 barre contro 1.782, con **1.606 in comune**: ~90% di sovrapposizione, il 6% di
armature diverse. **Su questa finestra `DriftMode 1` non cambia l'ordine di grandezza
dell'edge.** La sua utilità vera è sull'IS, dove la divergenza fra i due modi è maggiore.

# Pre‑registrazione 8 — la soglia di WR sull'IS (15/10/2026, prima del run)

Stage 2 sull'IS **2020‑01‑01 → 2024‑12‑31**, `DriftMode 0`, 1 contratto, $7,50/contratto,
`SizeMode 1`, `ExitMode 0`. Più il run `DriftMode 1` a `DriftThreshAtr 0.56` come variante
pre‑registrata.

Tenendo il R:R realizzato a 0,596 e il DD_R a 24,5, il criterio `RATIO ≥ 1` richiede:

| DD_R | E richiesta | **WR richiesto** |
|---|---|---|
| **24,5** (misurato) | 0,1103 | **≥ 69,6%** |
| 21 (se le uscite fossero più binarie) | 0,0945 | ≥ 68,6% |

**La soglia è WR ≥ 70% sull'IS.** Osservato sul 2026: 64,4%. Serve che lo stop a 0,38 ATR
invece di 0,22 porti **+5,6 punti di win rate**.

Se l'IS dà WR < 68%, la strategia è chiusa: nessuna variante pre‑registrata muove il WR di
quell'ordine, e il resto del profilo è già misurato.

---

# Stage 2 — IS 2020‑2024: **Gate 2 fallito. Cimitero, causa B.**

3.499 trade, 2020‑01‑02 → 2024‑12‑31, 1 contratto, $7,50/contratto. Report in `reports/`.

| | `DriftMode 0` (autore) | `DriftMode 1` (ATR 0,56) | ×10 |
|---|---|---|---|
| n | 3.499 | 3.499 | 3.499 |
| net | $194.110 | $174.150 | $1.953.565 |
| avg trade | **$55** | $50 | $558 |
| PF | 1,117 | 1,105 | 1,118 |
| **WR** | **63,5%** | 63,1% | 63,5% |
| R:R realizzato | 0,640 | 0,644 | 0,641 |
| null | 61,0% | 60,8% | 60,9% |
| **eccesso** | **+2,6 pp** | +2,3 pp | +2,6 pp |
| **t** | **3,01** | 2,70 | 3,03 |
| E | 0,0543 | 0,0504 | 0,0546 |
| R per micro | $130 | $128 | $130 |
| DD per micro | $3.309 | $3.634 | $3.309 |
| DD_R | 25,5 | 28,3 | 25,5 |
| **RATIO** | **0,47** | **0,40** | 0,48 |

## La soglia pre‑registrata e il verdetto

Era scritta prima del run: **WR ≥ 70%** per passare, **chiusa sotto 68%**. Misurato
**63,5%**. Il verdetto è automatico.

## La mia previsione era sbagliata, e il motivo è una regola

Avevo scritto che il WR sarebbe salito dal 64,4% del 2026 a ≥70% sull'IS, perché lo stop
fisso di 80 punti vale **0,38 ATR nell'IS** contro **0,22 nel 2026**. Misurato: da 64,4% a
**63,5%**. Praticamente invariato, anzi leggermente più basso.

**L'errore è identificabile.** Guardavo solo lo stop. Ma il **target è fisso anch'esso** (40
punti long, 50 short), quindi cambiando volatilità **entrambe le gambe** scalano insieme. E
la probabilità di primo tocco in un random walk è **S/(S+T)**, che dipende solo dal
*rapporto*: è invariante di scala.

> **Regola che resta**: quando stop **e** target sono entrambi fissi in punti, il win rate è
> approssimativamente **invariante al regime di volatilità**. Cambia il tempo di risoluzione,
> non l'esito.
>
> È il contrario del caso Gold, dove lo stop *era* l'ampiezza del range — scalava con la
> volatilità — mentre i costi restavano fissi. Là il regime cambiava tutto, qui niente.

## Lo sblocco del drift non aiuta — e questo chiude anche il blocco

`DriftMode 1` a `DriftThreshAtr 0.56` dà **RATIO 0,40 contro 0,47**: peggio. WR 63,1%
contro 63,5%, DD_R **28,3** contro 25,5.

Il blocco era reale (la soglia in % oscilla di un fattore 3,6 in ATR anche dentro 100
giorni), ma **ripararlo non migliora l'economia**. Era un difetto di coerenza, non la causa
della debolezza. Il blocco si può considerare chiuso: la risposta è «sistemato, e non
cambia niente».

## Il limite ottimistico

DD_R 25,5 impone R ≤ $2.000/25,5 = **$78 per micro**. A quel R:

- edge lordo = 0,0543 × $78 = **$4,24 per micro**
- meno $2 di costo → **$2,24 netti**, contro i **$7** richiesti dal Gate 2

**Anche a costi esattamente zero** l'edge sarebbe $4,24 contro $7: manca un fattore **1,65**.
Morta anche con trading gratuito.

## ✉️ Causa di morte: **B** — e è il caso più informativo dei sei

**L'edge è reale.** `t = 3,01` su 3.499 trade: è la **prima strategia della pipeline con un
edge statisticamente solido**. Non è rumore come Gold (t 0,92) o VWAP Pullback (t 0,23).
Nessun anno vale più del 50% del profitto (28/22/25/4/22%).

E non basta. Il criterio chiede **E ≥ 0,115**; questa ha **E = 0,0543** con t = 3,01.

> **Un edge statisticamente solido è ancora 2,1 volte troppo piccolo per il conto.**

È la prova più forte che abbiamo che il vincolo che morde non sono le strategie.

## Gate 1, chiuso con un'annotazione

Il test ×10 dà: **Gross Profit esattamente 10,000000** e **Max Strategy Drawdown esattamente
10,000000**; **Gross Loss 9,992462** (scarto dello **0,075%**) e commissioni 9,997428.
Conteggio trade, WR e conteggi delle uscite **identici**.

Non è il difetto della classe `CurrentContracts` — quello darebbe un fattore 10 su trade
specifici, non uno 0,075% diffuso — e la sequenza dei trade è identica. **Non ho una
spiegazione completa dello 0,075%**: lo annoto invece di archiviarlo come «passato».

---

# Stage 5 — OOS 2025-2026: pre-registrazione (15/10/2026)

**Perche siamo qui.** Lo split prop/live (`mc/docs/prop_vs_live.md`) ha tolto da Gate 2 i
criteri dei soldi propri. Rigiudicata col solo metro prop questa strategia **passa**:
**t 3,01 · WR 63,5% · R:R 0,64**, e il WR sta dentro la banda **54-72%** che il corso
dichiara (Live 005, 1585), a un punto e mezzo dall'esempio che deploya (~65%, avg netto $77,
Live 002, 244-252).

**Cosa l'aveva uccisa.** La soglia `WR >= 70%` pre-registrata allo Stage 1, derivata dal
nostro `RATIO = E x DDcap / (DD_R x (soglia + costo))`. Due difetti di quella formula:

1. il termine `soglia` **e** il criterio live dei $7/micro, che oggi e in stand-by;
2. chiede di **sopravvivere al drawdown storico di cinque anni** col rischio compresso
   dentro l'MLL. Una eval non e quello: e un **primo passaggio su finestra corta,
   ripetibile**. Il corso lavora col **39% di pass rate per tentativo** (Live 003, 107)
   perche su quattro tentativi diventa **92,6%** (Live 004, 238).

Il RATIO rispondeva con una formula, nella versione piu severa, alla domanda che il corso
affida al **simulatore**. Lo Stage 7 lo sostituisce.

## Configurazione: congelata, nessun parametro si tocca

`DriftMode 0` · `DriftThreshPct 0.10` · `MALen 20` · `DriftLen 4` · `PullbackWindow 6` ·
bracket **80 / 40 / 50** · `MaxLossesPerDay 2` · `EntryMode 0` · `TriggerMode 0`

Dati: **@NQ 5m + 15m (data2)**, serie **non back-adjusted** (il difetto trovato il 29/09 e
decisivo qui, perche `driftPct` usa una percentuale del prezzo).
Costi: **$7,50/contratto/lato** + **2 tick di slippage sullo stop** (`StopSlipTicks 2`),
identici all'IS.
Finestra: **2025-01-01 → 2026-10-15**. Una volta sola.

## Criteri, scritti prima del run

| criterio | soglia |
|---|---|
| **t** | **>= 1,3** (il livello del corso, «≤10% simulazioni negative») |
| WR | >= 50%, e **dello stesso ordine** del 63,5% dell'IS |
| R:R | 0,5-1 |
| DD | <= 1,5x quello dell'IS |

**Kill:** `t < 1,3` → cimitero definitivo, come VaultBreak. Nessun ritocco, nessuna variante
di recupero.

## Attesa dichiarata

**WR fra 62% e 65%.** Motivo: stop **e** target sono entrambi fissi in punti, quindi
P(primo tocco) = S/(S+T) dipende dal **rapporto** e non dalla scala → il WR e **invariante al
regime di volatilita**. E la regola misurata tre volte (Gold, VaultBreak, e questa stessa
strategia fra 2026 al 64,4% e IS al 63,5%).

Se il WR crolla sotto 55%, **non e il regime**: e che l'edge non c'era. Quella e la
falsificazione, e non va spiegata via.

## Riserva economica, registrata ora

L'obiezione del RATIO non e nulla e non va dimenticata: con **DD_R 25,5** il drawdown ammette
**R <= $78/micro**, dove l'edge netto vale **~$2,24/trade**, cioe **~$1.568/anno per micro**
contro **$3.000** di target — e il rapporto **non migliora** aumentando i micro, perche
drawdown e profitto scalano insieme.

Se il simulatore dello Stage 7 conferma quel tempo, la strategia muore **la'**. Ma muore con
la risposta giusta — pass rate e tempo di passaggio su piu tentativi — invece che con una
stima su percorso medio.

## Stage 5 — ESITO: PASSA (15/10/2026)

Report: `reports/DPB_S5_OOS_2025-2026.xlsx`. Range verificato dalle Settings:
**2025-01-02 -> 2026-10-15**, 1 contratto su tutti i 1.439 trade, commissione $7,50/contratto,
Bar Magnifier Enabled 1 Minute. Preliminari tutti puliti.

| | IS 2020-2024 | **OOS 2025-2026** | |
|---|---|---|---|
| n | 3.499 | **1.439** | 700/anno -> 808/anno |
| avg trade | $55,48 ± 18,44 | **$57,32 ± 30,74** | **piu alto** |
| WR | 63,5% | **64,5%** | attesa dichiarata 62-65%: **centrata** |
| R:R | 0,64 | **0,61** | |
| t | 3,01 | **1,86** | soglia 1,3 |
| PF | 1,117 | **1,111** | |
| DD chiusi | $31.670 | **$38.125** | 1,20x, soglia 1,5x |

**Non si e' deteriorato niente.** Il controllo piu stringente: a edge invariato il t scala
con la radice di n, quindi da 3,01 su 3.499 trade ci si aspetta **1,93** su 1.439. Misurato
**1,86**. L'edge dell'OOS e statisticamente indistinguibile da quello dell'IS — il t piu
basso e **solo** l'effetto del campione piu piccolo, non un decadimento.

E l'attesa sul WR era pre-registrata e si e' verificata: stop **e** target fissi in punti ->
P(primo tocco) = S/(S+T) -> WR invariante al regime. 63,5% -> 64,5%.

**Prima strategia della pipeline a superare un out-of-sample.** Le altre sei: tre senza edge,
una falsificata sull'OOS (VaultBreak), due mai arrivate qui.

### La riserva economica, ora col numero dell'OOS

Resta in piedi ed e' la domanda vera dello Stage 7:

- avg **$5,73 per micro** x **808 trade/anno** = **$4.634/anno per micro**
- DD **$38.125 = 26,3 R** -> **$3.812 per micro**, contro un **MLL di $2.000**

Cioe: **un singolo MNQ ha un drawdown storico che sfonda l'MLL di 1,9 volte.** Il DD_R e
confermato dall'OOS (26,3 contro 24,4 dell'IS) quindi non e' un artefatto del campione.

**Ma questa non e' la domanda della eval**, ed e' l'errore che il RATIO faceva: la eval non
chiede di sopravvivere al drawdown peggiore di due anni, chiede **la probabilita di toccare
+$3.000 prima di -$2.000 partendo da zero**, su una finestra corta e con **piu tentativi a
$100**. A $4.634/anno per micro il target da $3.000 e a ~7,8 mesi con 1 micro, e scalando i
micro il tempo si accorcia ma il drawdown cresce insieme.

**Lo decide il simulatore, non una formula.** Stage 7, sulla lista di trade di questo OOS.

## Stage 7 — simulazione: PASSA a 2 micro (15/10/2026)

Simulatore: `mc/docs/prop_sim.py`. Regole LucidFlex 50k verificate sui transcript — conto
$50.000, target +$3.000, MLL $2.000 trailing EOD con lock a $50.100, flat EOD, **nessuna
regola di consistency** (Live 002, 444: *"you don't have a consistency rules, but you have a
minimum profit day, on 50K is $150 per day"*, e quel minimo riguarda il payout da funded, non
il passaggio). Costo micro **$1,50/round-turn**: il P&L del report e NQ full-size con $15/RT
dentro, si torna al lordo, si divide per 10, si applica il costo del micro.

**Conservativita**: il breach si controlla sull'**escursione dentro il trade** (colonna
`Drawdown ($)` del report), non sulla chiusura — e la conservativita che il corso ha aggiunto
in Live 003 (*"we consider the path inside the day as well"*).

### Il risultato, e regge su entrambi i campioni

| piano | pass/tentativo | gg mediani | entro 3 | entro 4 | tempo atteso |
|---|---|---|---|---|---|
| **2 micro, finestra 60 gg** | **42,5% IS / 42,3% OOS** | 29 | 81% | **89%** | **~2,5 mesi** |
| 1 micro, senza limite | 62,2% IS / 58,1% OOS | 105 | **95%** | 98% | ~8 mesi |
| 3 micro | 41,1% | 15 | 80% | 88% | ~1,5 mesi |

A 2 micro **IS e OOS danno lo stesso numero** (42,5 e 42,3). Il simulatore non sta leggendo
rumore. E robusto anche ai costi: a $2,50/RT invece di $1,50 il pass rate scende da 41,6% a
**38,2%**.

**Allineato col corso**: 38-47,9% per tentativo e 85-92,6% entro quattro (Live 003, 107 e
Live 004, 237-238), col playbook da **$400** (tre tentativi piu attivazione).

### Il RATIO era sbagliato, e di quanto

Diceva: RATIO 0,47, **2,1 volte troppo piccola**, e *"anche a costi esattamente zero manca un
fattore 1,65"*. Il simulatore dice **42% per tentativo, 89% entro quattro, $400, ~2,5 mesi**.

Il difetto era quello registrato prima del run: chiedeva di sopravvivere al drawdown storico
di cinque anni (26,3 R) quando la eval chiede di fare **+$3.000 (10,3 R a 2 micro) prima di
-$2.000 (6,9 R)** su una finestra corta. A 2 micro il drawdown storico vale $7.627 contro un
MLL di $2.000 — sfonda di 3,8 volte — **e il pass rate e comunque 42%**, perche quel
drawdown si forma in cinque anni e il tentativo dura due mesi.

### Le due riserve, scritte e non risolte

**1. Il drawdown corrente.** La curva e a **$3.341 dal massimo per micro, 98esimo percentile**
della sua distribuzione storica, contro un massimo di $3.812. Il corso mette in panchina
**questa esatta strategia** per questo motivo (Live 004, 152: *"among these three strategies I
would bench right now the drift pullback"*). Misurato sull'IS condizionando alle partenze da
drawdown oltre il 95esimo percentile: **2 micro/60 gg da 67%**, **1 micro/250 gg da 7%**. Si
ribalta col piano, e in entrambi i casi le finestre indipendenti sono ~5-20. **Non
rispondibile con questo storico.** Vale come riserva: se si parte, si parte col piano
**veloce** (2 micro, finestra corta), non col lento.

**2. Una sola strategia.** Live 004: *"takeaway number one: **don't run a single strategy even
in the evaluation phase**, that is going to put you at a disadvantage"*. Coi suoi numeri, un
basket da 45,8% al primo tentativo contro 38% di una singola, e 84,3% contro 77,2% entro sei.
Non contraddice la nostra regola «una alla volta», che riguarda lo **sviluppo**: si sviluppa
una per volta, si **deploya** in gruppo.

## Porting su @YM: la forma si trasferisce, l'edge no (18/10/2026)

Report: `reports/DPB_S2_IS_PORT-YM_2020-2024.xlsx`. IS 2020-2024, 3.393 trade, $6,75/lato,
Bar Magnifier 1 min, Globex 24h. Stop riscalato per ATR a **129 punti** (0,381 del range
mediano di YM, la stessa frazione che 80 punti valgono su NQ), target 65 e 81.

| | **@NQ** | **@YM** |
|---|---|---|
| n | 3.499 | 3.393 |
| **WR** | **63,5%** | **61,8%** |
| **R:R** | **0,64** | **0,62** |
| caso (1/(1+R:R)) | 61,0% | 61,7% |
| **eccesso sul caso** | **+2,52 pp** | **+0,07 pp** |
| expectancy | **0,0414 R** | **0,0012 R** |
| avg trade netto | **$55,48** | **$1,54** |
| **t** | **3,01** | **0,20** |

**La scalatura per ATR ha funzionato come doveva**: WR 61,8% contro 63,5% e R:R 0,62 contro
0,64. **La geometria si trasferisce quasi perfettamente.**

> **Ma l'eccesso sul caso passa da +2,52 pp a +0,07, e l'expectancy e 34 volte piu piccola.**
> **L'edge e di NQ, non del metodo.**

E la conferma piu' netta che potessimo avere dell'avvertenza del corso — *"this same strategy
logic does not automatically work across asset classes"* (Lesson 3, 18:59) — e vale perfino
fra due indici azionari americani correlati 0,8-0,95.

**Conseguenza**: la seconda gamba non si ottiene replicando la prima altrove. DriftPullback
resta l'unica, e il suo edge e legato a qualcosa che NQ ha e YM no — probabilmente il fatto
che il drift di un'ora su NQ sia piu' persistente, ma **non l'abbiamo misurato e non si
specula**.

## Stage 7 rifatto col degrado (18/10/2026): e il numero che decide

Aggiunti al simulatore gli **scenari di degrado**, che il Colab del corso ha e il mio non
aveva: *e se dal vivo rende meno del backtest?* Una frazione dei vincenti viene trasformata in
perdite vere e tutti i P&L vengono ridotti.

### I due piani, a confronto

| scenario | **2 micro, 60 gg** | | **1 micro, senza limite** | |
|---|---|---|---|---|
| | pass | entro 4 | pass | entro 4 |
| come da backtest | **42,7%** | **89,2%** | **58,4%** | **97,0%** |
| WR −3 pp, P&L −10% | **24,2%** | 67,0% | **22,2%** | 63,3% |
| WR −5 pp, P&L −15% | **12,4%** | 41,1% | **4,3%** | 16,1% |
| WR −5 pp, P&L −25% | 9,5% | 32,8% | 5,0% | 18,7% |
| WR −8 pp, P&L −30% | 1,5% | 5,7% | **0,0%** | 0,2% |

### Due cose che si leggono qui e non si vedevano prima

**1. La strategia e fragile al degrado.** Bastano **3 punti di win rate e un −10% di P&L** per
**dimezzare** il pass rate. A −5 punti crolla. Il motivo e strutturale: l'expectancy e
**0,0414 R**, togline un po' e va a zero. Non e un difetto di questa strategia, e la
conseguenza di un edge sottile — che e l'unico tipo di edge che abbiamo mai trovato.

**2. Il piano veloce e piu' ROBUSTO di quello lento**, anche se parte da un pass rate piu'
basso. A −5 punti di WR: **12,4% contro 4,3%**, e a −8 punti **1,5% contro 0,0%**.

**Perche'**: il piano lento ha bisogno di ~77 giorni di macinatura, e vive sull'**accumulo**
dell'edge. Degrada l'edge e la lunga marcia diventa un lento sanguinamento dentro l'MLL. Il
piano veloce chiude in 22 giorni mediani e vive piu' sulla **varianza**, che il degrado non
toglie.

> **Se si parte, si parte col piano veloce: 2 micro, finestra corta.** Lo diceva gia' la
> riserva sul drawdown corrente, ora lo dice anche il degrado.

### Cosa serve sapere prima di spendere i $400

La domanda non e' «qual e' il pass rate» ma **«quanto e' probabile il degrado»**. Tre cose che
sappiamo:

- l'OOS ha dato **WR 64,5% contro il 63,5% dell'IS**: il win rate e' stato **stabile**;
- i costi sono **verificati** sul listino Lucid, non stimati;
- **ma la curva e' al 98esimo percentile del suo drawdown**, e partire da li' e' gia' una
  forma di scenario degradato — quello che il corso chiama mettere in panchina una strategia.

**Con $400 di budget e 4 tentativi: 89% se il backtest regge, 67% se degrada di 3 punti, 41%
se degrada di 5.**

## DriftPullback per regime di gamma (23/10/2026) — informazione sul rischio, non una modifica

GEX della sera prima (SqueezeMetrics), terzili fissati sull'IS: basso < 2,08 mld, alto ≥ 5,01.
**L'OOS e' gia' stato usato: qui non si cambia la strategia, si calibra l'aspettativa.**

### P&L per terzile

| GEX di ieri | IS avg | IS WR | OOS avg | OOS WR |
|---|---|---|---|---|
| basso | $73,25 (t 2,37) | 66,5% | $90,71 (n 196) | 66,3% |
| medio | $49,80 | 62,6% | $52,99 | 64,9% |
| alto | $38,71 (t 1,18) | 60,7% | $51,64 (n 867) | 63,9% |
| **basso − alto** | **+$34,54, 0,77 es** | | **+$39,07, 0,40 es** | |

**Monotono in tutti e due i campioni, nella direzione del meccanismo** (momentum migliore col
gamma basso), sia sull'avg sia sul win rate. **Ma non significativo**: la differenza sta sotto
un errore standard in entrambi.

**E positiva in tutti e tre i terzili, in tutti e due i campioni.** Non c'e' nessun regime in
cui la strategia perda.

### Pass rate per regime (2 micro, finestra 60 giorni, iid)

| | giorni | per tentativo | entro 4 |
|---|---|---|---|
| OOS, tutti | 456 | 42,0% | 88,6% |
| **OOS, solo GEX alto** | 287 | **40,2%** | **87,2%** |
| OOS, solo GEX basso | 56 | 53,0% | 95,1% |
| IS, tutti | 1.275 | 41,9% | 88,6% |
| **IS, solo GEX alto** | 423 | **33,0%** | **79,8%** |
| IS, solo GEX basso | 426 | 51,3% | 94,4% |

**Dal 2025 il regime e' alto il 63% dei giorni** (285 su 453; basso 57, medio 111). Il numero
realistico per la eval che parte il 26/10 non e' quindi il 42%/89% medio, ma quello dei giorni ad
alto gamma: **fra 33% e 40% per tentativo, fra 80% e 87% entro quattro**. L'OOS, piu' vicino al
regime attuale, sta in alto in quella forchetta.

### Cosa se ne fa, e cosa no

- **Non si spegne nei giorni ad alto gamma**: rende anche li'.
- **Non si cambia la size per regime adesso**: la differenza non e' significativa e l'OOS e'
  gia' stato usato. Se mai, e' un'ipotesi per una v2 — size piu' alta col GEX basso — da
  validare **sul live**, pre-registrandola prima.
- **Si guarda il GEX ogni sera** come informazione: un tentativo che capita in un periodo di
  gamma basso (mercati in tensione) ha probabilita' migliori, uno in un periodo calmo ad alto
  gamma peggiori.
