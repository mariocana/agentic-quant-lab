# SPEC — Counter Trend di Unger, porting su GC (Stage 0)

**Ipotesi**: nella mattina di Londra, un eccesso oltre le bande di Bollinger contro la
direzione del giorno prima rientra. Se ieri il mercato ha chiuso in rialzo e stamattina il
prezzo scende sotto la banda inferiore e poi ci rientra, si compra; specularmente short.
**Perché**: all'apertura di Londra gli ordini accumulati in Asia producono spinte che spesso
sono rumore di liquidità; quando vanno contro il movimento del giorno prima vengono
riassorbite. Chi perde: chi insegue il primo movimento della sessione europea.
**Fonte**: Andrea Unger, *Trading System Supremacy*, modulo 5. Codice `DevelopRev` nel video
5x01 (compilato il 21/01/2016), parametri finali nel 5x02: **`DevelopRev(14, 15, 40, 40, 300,
8, 2359, 0, 0.01, 0, 20, 2)`**, **GBPUSD** forex 30 min, dati TradeStation, grafico in ora di
New York. Risultato mostrato, 2008 → gennaio 2016 su 100.000 GBP: net $157.956, PF 1,74, max
DD $11.708, **commissioni e slippage $0**.

## Perché GC e non GBPUSD

Su Lucid il forex esiste solo come futures interi (6B: 62.500 GBP): stop di 100 pip = $625 a
contratto contro $500 di soglia, drawdown di Unger riportato a un 6B ~$7.300 contro un MLL di
$2.000. **Causa B per costruzione**: testare 6B ha senso solo per un conto molto più grande,
quindi non si testa (decisione dell'utente, 18/10/2026).

La strategia è legata a **Londra**, non al pound. Il candidato naturale è l'**oro**: Londra è
la sua piazza principale, la mattina europea è uno dei suoi momenti più liquidi, e c'è il micro
(MGC). **ES e YM** si girano solo come esplorazione: per loro 02:00–05:00 CT è la sessione
notturna e l'ipotesi si trasferisce male; un risultato buono lì andrebbe spiegato, non preso.

## Regole

| | |
|---|---|
| Famiglia | counter trend / ritorno dentro le bande, long e short |
| Strumento · TF | **@GC** (sviluppo) → **MGC** (÷10) · **30 min** · Globex 17:00–16:00 CT senza pause, chart CT |
| Esplorativi | @ES → MES, @YM → MYM, stesse regole |
| Bande | Bollinger sul close, 20 periodi, 2 deviazioni (Unger) |
| Finestra | dalla barra delle **02:00 CT** (= 03:00 New York) per le prime 8 barre: segnali da 02:30 a 05:00 CT; domenica esclusa |
| Long | close che incrocia al rialzo la banda inferiore, **ieri chiusura in rialzo** (pattern 14), **ieri non outside bar** (no 40) |
| Short | close che incrocia al ribasso la banda superiore, **ieri chiusura in ribasso** (15), no 40 |
| Stop | **0,65% del close sulla barra del segnale**, congelato per il trade |
| Target / uscita a tempo | nessuno / **nessuna** (variante A): stop o inversione |

**Lo stop, regola unica senza ottimizzazione.** Gli 0,01 di Unger su GBPUSD, con una media
2008–2016 di ~1,55, valevano lo 0,65% del prezzo. Si porta la stessa frazione: è l'unico
parametro che cambia, e non si ottimizza. Bande, finestra e filtri restano quelli del video.

| | prezzo | stop 0,65% | per micro |
|---|---|---|---|
| GC | ~4.100 | ~27 pt | **~$267 per MGC** |
| ES | ~7.800 | ~50 pt | ~$250 per MES |
| YM | ~45.000 | ~290 pt | ~$146 per MYM |

Tutti sotto la soglia del peggior trade ($500 per micro).

**Fuso orario.** Il grafico di Unger è in ora di New York (la sessione della domenica parte
alle 17:00 e dura poche ore: l'apertura del forex alle 17:00 ET). 03:00 ET = **02:00 CT**.

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi. Tutto dopo gennaio 2016 è fuori
campione per l'autore; per GC/ES/YM lo è anche lo strumento.

## Varianti pre‑registrate

| variante | `FlatEOD` | ruolo |
|---|---|---|
| **A** (originale) | 0 | regole di Unger, posizione anche overnight |
| **B** (prop) | 1 | flat a fine sessione (16:00 CT): rispetta "flat prima della chiusura" |

## Worst day strutturale
- **B**: entrate solo fra 02:30 e 05:00, al massimo un'inversione nella finestra: **2 stop**
  = ~$534 per MGC, più costi e slittamento. Sopra i $500 della soglia del peggior *trade*,
  ma è un worst *day*: va letto contro l'MLL ($2.000), e regge.
- **A**: non limitato. Le posizioni restano aperte giorni e attraversano i gap della domenica.

## Soglie del Gate 2 (LucidFlex 50k, ÷10 per il micro)

| Metrica | GC | ES | YM |
|---|---|---|---|
| avg trade netto (≈5 × costo andata e ritorno) | ≥ $140 | ≥ $140 | ≥ $75 |
| max DD sul contratto pieno | ≤ $10.000 | ≤ $10.000 | ≤ $10.000 |
| peggior trade sul contratto pieno | ≤ $5.000 | ≤ $5.000 | ≤ $5.000 |
| n trade IS, PF, WR, R:R, annuale | come pipeline: ≥ 200, ≥ 1,2, ≥ 55%, 0,5–1, nessun anno > 50% | | |

**Costi** per lato, slippage incluso: GC **12.5$**, ES **15$**, YM **7.5$** per Contract,
campo slippage a 0.

**Kill**: gate della pipeline, giudicati su **GC**. ES e YM non promuovono la strategia da
soli: se passano solo loro, va scritto perché un'ipotesi "di Londra" funzionerebbe sugli
indici USA nella loro notte, prima di andare avanti.

## Note
- **Back‑adjustment**: lo stop in percentuale si calcola sul prezzo del continuo aggiustato.
  Su GC il contango sposta i livelli vecchi: allo Stage 1 si confronta il close di una
  barra del 2020 con il prezzo reale di allora. Se lo scarto supera ~10%, lo stop in
  percentuale nel 2020 è distorto della stessa misura e va annotato.
- **Session template**: GC con il template `COMEX: Metals Futures (Electronic)` perdeva le
  barre fra 07:45 e 14:15 (GAR, Stage 1). Qui serve 17:00–16:00 senza pause, come per ES.

---

# Stage 2 — **Gate 2 fallito su GC** (23/10/2026) → **cimitero, causa A — edge assente**

IS 2020–2024 (GC dal 21/01/2020), 30 min, template 17:00–16:00, 1 contratto, costi della
spec, Bar Magnifier 1 min. Report in `reports/CT_S2_*_IS.xlsx`. Il corpo sopra è la
pre‑registrazione e non si riscrive.

| run | n | WR | avg netto | t | PF | DD chiusi | lordo/trade (t) | uscite |
|---|---|---|---|---|---|---|---|---|
| **GC A** | 213 | 31,9% | −$129 | −0,68 | 0,88 | $68.840 | −$104 (−0,55) | 137 stop, 75 inversioni |
| **GC B** | 279 | 43,4% | −$200 | **−2,50** | 0,69 | $62.135 | **−$175 (−2,19)** | 82 stop, 197 fine sessione |
| ES A | 228 | 25,9% | +$6 | 0,02 | 1,00 | $45.970 | +$36 (0,14) | 159 stop, 68 inversioni |
| ES B | 308 | 44,8% | +$52 | 0,50 | 1,08 | $23.853 | +$82 (0,79) | 98 stop, 210 fine sessione |
| YM A | 194 | 23,2% | −$64 | −0,33 | 0,93 | $40.665 | −$49 (−0,25) | 143 stop, 50 inversioni |
| YM B | 276 | 46,4% | +$89 | 1,01 | 1,17 | $12.995 | +$104 (1,18) | 97 stop, 179 fine sessione |

**Verdetto su GC (pre‑registrato come strumento di giudizio).** La variante A perde (t −0,68);
la B perde in modo significativo (t −2,50) e **perde anche prima dei costi** (lordo −$175 a
trade, t −2,19). Gate 2 fallito su avg, PF, WR, DD (A: $6.884 per MGC) e annuale.

**Le inversioni ci sono.** Il dubbio dello Stage 1 (13 trade su 13 a stop in 106 giorni) non
spiega il risultato: su cinque anni la variante A di GC esce per inversione in 75 trade su
213 (35%). La strategia ha la meccanica di Unger e sull'oro non funziona.

**ES e YM non la salvano.** La regola pre‑registrata dice che gli esplorativi non promuovono
la strategia da soli. YM B è il migliore dei sei run (t 1,01, PF 1,17, tutti e cinque gli anni
positivi), ma:
- su sei run il migliore con t ≈ 1 è quello che ci si aspetta dal caso (il massimo atteso di
  sei estrazioni casuali è circa 1,3);
- fallisce comunque il Gate 2: WR 46,4% (≥ 55%), R:R 1,36 (0,5–1), PF 1,17 (≥ 1,2), DD
  $1.300 per MYM (≤ $1.000);
- per gli indici USA la finestra 02:00–05:00 CT è la sessione notturna: l'ipotesi "di Londra"
  non ha una ragione per funzionare lì.

**Sul risultato di Unger** (GBPUSD 2008–2016, PF 1,74): era a costi zero e su un'altra valuta.
Non è stato smentito su GBPUSD, che non abbiamo testato perché su Lucid è causa B per
costruzione; il porting sull'oro, con la stessa regola di stop, non regge.

**Back‑adjustment**: il close di @GC al 02/01/2020 non è stato annotato. Non cambia il
verdetto: GC B perde anche prima dei costi, e lo stop in percentuale incide solo sulla
dimensione dei trade, non sul segno.

**Cosa la riaprirebbe**: un conto che regga un 6B intero (stop $625, DD stimato ~$7.300) e un
test su 6B o GBPUSD con costi veri. Nessuna variante pre‑registrata la riapre sull'oro.
