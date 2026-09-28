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
5. **Ingresso su stop oltre l'estremo della barra di pullback** invece che *next bar at
   market*: setup armato, barra contraria → buy‑stop sopra il massimo di quella barra
   (mirror per gli short). Il drift deve **riprendere** prima che si sia dentro, quindi
   filtra i pullback che proseguono. Idea dal Triple Screen di Elder (1993), stessa
   architettura dual‑timeframe di questa strategia — vedi `mc/education/books/NOTES_elder.md`.
   Costo noto da misurare, non da assumere: si perdono i trade in cui il rimbalzo riparte
   subito senza superare quel massimo. Risolve anche, di fatto, la "barra d'ingresso
   scoperta" (l'ingresso diventa un livello noto in anticipo).

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
