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
