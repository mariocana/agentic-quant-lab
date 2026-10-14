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
