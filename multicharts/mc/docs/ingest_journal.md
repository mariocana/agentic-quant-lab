# Journal degli ingest — cosa abbiamo letto e perché l'abbiamo tenuto o scartato

Registro di ogni documento che entra in `mc/education/books/`, `mc/ideas/` e simili.
Serve a due cose, la seconda più importante della prima:

1. sapere **cosa ne è uscito** (idea entrata in pipeline, variante pre‑registrata, niente);
2. sapere **cosa abbiamo già guardato**, per non rileggere fra sei mesi lo stesso libro
   arrivando alla stessa conclusione.

## Come si usa

- Ogni documento ingerito ha **una riga** nella tabella, anche se non l'abbiamo ancora letto.
- I documenti con una valutazione vera hanno anche un file `NOTES_<nome>.md` **accanto al
  documento**, non qui: qui c'è solo la sintesi in una riga e il link.
- **Il verdetto è definitivo salvo dati nuovi.** Se una cosa è `scartato`, non si rivaluta
  senza un motivo scritto (materiale nuovo dell'autore, cambio di contesto nostro). È la
  stessa logica del cimitero dello Stage 5.

**Vocabolario dei verdetti** (uno solo per riga):

| Verdetto | Significato |
|---|---|
| `scartato` | Niente da prendere. Non si riapre. |
| `playbook` | Niente per la pipeline algo, ma materiale valido per il **trading discrezionale**: la sintesi va scritta pensando a chi la userà a mano, non a chi la codificherà. |
| `idee estratte` | Il documento nel complesso non serve, ma qualcosa è entrato (variante, filtro, nota metodologica). |
| `in pipeline` | Ne è nata una strategia in `mc/strategies/`. |
| `in coda` | Vale la pena, ma è bloccato da qualcosa (dati, strumenti, priorità). Il blocco va scritto. |
| `da valutare` | Ingerito e non ancora letto. |

**Regola sul protocollo**: il materiale esterno può produrre **strategie e varianti**, mai
modifiche ai gate. Il protocollo resta quello del corso (`pipeline_prop.md`).

---

## Registro

| Data | Documento | Cosa è | Verdetto | Cosa ne è uscito |
|---|---|---|---|---|
| 2026‑09‑28 | [Alexander Elder — *Trading for a Living* (1993)](../../education/books/NOTES_elder.md) | Classico discretionary: psicologia, analisi grafica, indicatori, Triple Screen, money management | **idee estratte** | Variante d'ingresso `EntryMode 1` di DriftPullback (stop oltre l'estremo del pullback, dal Triple Screen). Force Index / Elder‑Ray annotati come candidati filtro Stage 4. **Scartate le divergenze** (si definiscono a posteriori). |
| 2026‑09‑28 | [Steve Palmquist — *Money‑Making Candlestick Patterns* (2008)](../../education/books/NOTES_palmquist_candlestick.md) | Pattern a candele **backtestati**, azioni USA daily | **idee estratte** | Variante `TriggerMode 1` di DriftPullback (barra di pullback con rifiuto). I pattern in sé non trasferiscono: universo azionario con selezione cross‑sectional, daily multi‑day contro il nostro flat EOD, metrica in ROI% senza costi. |
| 2026‑09‑29 | [*Class summary Freddy 19.05* — GEX / GEXBot](../../ideas/NOTES_gex_freddy.md) | Note di una lezione: gamma exposure come mappa operativa su NQ/NDX/QQQ, letta con tape e order flow | **playbook** | Fuori dalla pipeline algo per quattro motivi: servono dati opzioni (GEXBot) **e** order flow, la regola è dichiaratamente discrezionale («leggere la reazione»), il payoff cercato è asimmetrico con upside lasciato correre (opposto al profilo prop), e prevede incrementi dopo conferma. Sintesi per il playbook scritta nelle note: meccanica del gamma (attrito / pin / accelerazione, call e put wall), i tre livelli di contesto, e il **calendario** OPEX / triple witching / VIXperation / JHEQX. Quest'ultimo è l'unico pezzo oggettivo e senza dati opzioni: annotato come possibile filtro di giornata, **non** pre‑registrato. |
| 2026‑09‑29 | `mc/ideas/…Liquidity_Gate_Complete_Academic_Specification_v5.0.docx` | Paper (Westbrook, lug 2026): classifica l'ambiente di liquidità su NQ in 5 tier per decidere quando il flusso istituzionale può forzare l'hedging dei dealer | **in coda** | **Blocco dati**: i criteri sono profondità del book a riposo, velocità di replenishment, gap nel book e **identificatori Market‑by‑Order** — cioè L3/MBO. Vedi `institutional_protocol_digest.md` §7: serve il Bridge (chiuso) + un'entitlement MBO separata, e resta aperto il problema della simmetria storico/live. Prima lettura, valutazione piena non fatta. |

| 2026‑10‑03 | [Unger — *Trading System Supremacy*, i due PDF + il `pattern base reference.docx`](../../education/unger/NOTES_unger_pdf.md) | Manuale EasyLanguage (19 pp.), e‑book *Profitable Trading Made Possible* (34 pp.), tabella di 42 pattern filtro | **idee estratte** | Le due strategie dell'e‑book non trasferiscono: daily, multi‑day, su DAX (Eurex) ed ES. Trasferisce il metodo. ⭐ **Il test del carattere del mercato**: girare lo stesso channel breakout con N da 1 a 15 e leggere la *forma* dei risultati prima di scrivere qualsiasi strategia — sul DAX profitti a quasi ogni N, sull'ES perdite a **ogni** N. Non l'abbiamo mai fatto su NQ, e tutte e sei le nostre strategie sono breakout. Nuove varianti Stage 4 da pre‑registrare: **stop/target in multipli del range medio** invece che in punti fissi, e **breakout dopo ritracciamento** (il livello rotto deve essersi formato qualche barra prima). Conferme: scelta del parametro dal grappolo e non dal picco, slippage dentro la commissione. Dal manuale, una parola sola ma pesante: **`SetStopContract`**, che renderebbe `SetStopLoss` per contratto e risolverebbe alla radice il bug dei run C/D di First5 — **da verificare col test ×10, non da adottare sulla fiducia**. Da non prendere: il processo di sviluppo dell'e‑book è tutto in‑sample, senza OOS né Monte Carlo. Bonus: i 42 pattern sono una riserva di filtri già scritti, con la coppia «sempre vero / sempre falso» che li rende un input ottimizzabile col base case dentro la griglia. |
| 2026‑09‑30 | [Morpheus — *Pro Trader Blueprint*, «2. I Modelli Intraday» video 1‑5](../../education/morpheus/ANALISI_modelli_intraday_1-5.md) | Il modello IVB: ORB/Initial Balance a 30 min sulla cash NY + conferma volumetrica (VSA, order flow), più profile framing | **idee estratte** | Il modello principale **è già nostro e già morto**: IVB = `ORB_Breakout` (stessa finestra 08:30‑09:00 CT, stesso TF, stessa scelta dei 30 min, stesso ingresso su chiusura piena), chiusa al Gate 3. Una sola idea nuova merita codice: **stop dietro la candela di breakout a 5 min invece che dietro il range** — attacca il vincolo che ha ucciso ORB e VaultBreak. È una **nuova Stage 0** (`IVB_Type1`), non una riapertura. Quattro varianti Stage 4 candidate: wick contenitiva, cutoff orario (già pre‑registrato), IB annidati, VSA sforzo/risultato. Order flow, big trades e l'indicatore DeepCharts: fuori stack (servono footprint bid/ask). Statistiche citate senza fonte, ma **misurabili da noi**. |
| 2026‑09‑30 | [`mc/ideas/ssrn-5598690.pdf`](../../ideas/NOTES_ssrn_batch.md) — *Evaluating the Parabolic SAR Strategy on Bitcoin* (Mesíček, nov 2025, 16 pp.) | Test del PSAR su BTC/USDT 2015‑2025, 1H e 1D, long/short/reversal | **scartato** | Risultato negativo e dichiarato: nessuna modalità batte il buy & hold. Backtest **senza fee e senza slippage** su 6.370 trade a 1H. L'unico risultato positivo («seasonality‑calibrated», Sharpe 1,35) è ottenuto restringendo l'operatività alle ore/giorni storicamente migliori **dopo** aver visto i risultati, senza OOS: è il fitting che vietiamo allo Stage 2. |
| 2026‑09‑30 | [`mc/ideas/ssrn-5580590.pdf`](../../ideas/NOTES_ssrn_batch.md) — *An Adaptive Multi‑Agent Bitcoin Trading System* (Singhi, UCL, 19 pp.) | Agenti LLM (DeepSeek‑r1) per allocazione su BTC, con «verbal feedback» al posto del fine‑tuning | **scartato** | **Contaminazione del test**: l'LLM legge news e sentiment su lug 2024–apr 2025, periodo dentro il suo training. Nove mesi di test, zero costi di transazione, e l'output è una decisione di un LLM — non una regola codificabile né backtestabile. Architettura interessante, strategia inesistente. |
| 2026‑09‑30 | [`mc/ideas/ssrn-6467818.pdf`](../../ideas/NOTES_ssrn_batch.md) — *Applied Econometrics and Algorithmic Trading* (59 pp., elaborato didattico) | ADF, volatility clustering, ARIMA/GARCH, poi MA crossover e RSI mean‑reversion con IS/OOS e walk‑forward | **scartato** | Era il candidato più promettente dei tre e non regge: **il documento si contraddice sui propri dati** (Parte I «gennaio 2025 – gennaio 2026», 364 righe; Parte IV «gennaio 2024 – gennaio 2026» con una walk‑forward da 21 finestre che ne richiederebbe oltre 700). RSI con 16 trade IS e 42 OOS su un periodo più corto. I costi ci sono (0,1%/lato) e l'impianto è concettualmente giusto, ma la nostra pipeline è più severa e gira su dati che esistono. |
| 2026‑09‑29 | `mc/education/stefano_serafini/Dax Trading Lab` | Corso in 3 lezioni (5h41) sul metodo MVP applicato al DAX + 16 anni di dati + due binari di strategia | **in coda** | **Blocco strumento, non dati**: il DAX è **Eurex** e su Apex non è negoziabile (verificato 29/09) → una strategia DAX non serve all'obiettivo prop. Trascrizioni fatte, analisi del metodo **rimandata**. Vedi il TODO sotto. |

### TODO — Dax Trading Lab (Serafini)

Sospeso, non scartato. Cosa c'è e perché potrebbe tornare utile:

- **Trascrizioni** delle 3 lezioni in `mc/education/stefano_serafini/transcripts/` — fatte, così
  quando si riprende non si riparte da 5h41 di video.
- **`DAX5m.txt` — il pezzo che vale a prescindere dal corso.** FDAX continuo a 5 min,
  **04/01/2010 → 11/02/2026**: 686.684 barre, 4.093 sessioni, ~42.500 barre l'anno senza
  buchi, zero barre a volume nullo, sessione 08:00–22:00 CET (168 barre/giorno, 73 nelle
  mezze giornate). Verificata la continuità: i dieci salti overnight maggiori sono tutti
  eventi macro reali (Brexit, Covid marzo 2020, Ucraina, dazi aprile 2025, referendum
  greco) e **nessuno cade su una scadenza trimestrale** → serie back‑adjusted pulita, non
  contratti grezzi incollati. Salto overnight mediano 23 punti. Ha **Up e Down volume
  separati**, cioè il delta: alimenta `UpTicks`/`DownTicks`.
- **`.ELD` e `.sef`**: binari. L'ELD è un export EasyLanguage importabile in MC ma
  normalmente protetto quando distribuito così; il .sef è un archivio serializzato di
  formato non riconosciuto. **Il sorgente della strategia probabilmente non c'è.**

**Quando riprenderlo** (uno dei due basta):
1. se si apre un ramo prop con un broker che dà Eurex (vedi «Ramo B» in `pipeline_prop.md`);
2. se serve un **banco di prova indipendente**: 16 anni di un altro mercato, con delta, su
   cui verificare se un'idea nata sul NQ regge altrove. Questo si può fare **adesso** e non
   dipende da Apex — è l'uso più probabile.

**Da valutare comunque per il metodo**: l'MVP di Serafini sembra un impianto suo
(Macro‑Volumi‑Probabilità) applicabile ad altri strumenti, non una ricetta solo‑DAX. È
questo, non la strategia DAX, la ragione per cui vale la pena tornarci.

## Inventario — cosa è fatto e cosa resta

Aggiornato **01/10/2026**. Una riga per documento anche quando non l'abbiamo letto: sapere
**cos'è** costa trenta secondi ed evita di riaprirlo per scoprire che non serve.

### `mc/ideas/` — ✅ tutto smarcato

Non resta niente da processare in questa cartella.

| File | Cos'è | Stato |
|---|---|---|
| `Class summary Freddy 19.05.pdf` | GEX / GEXBot su NQ‑NDX‑QQQ | **playbook** → [`NOTES_gex_freddy.md`](../../ideas/NOTES_gex_freddy.md) |
| `…Liquidity_Gate…v5.0.docx` | Tier di liquidità su NQ (Westbrook) | **in coda** — blocco dati L3/MBO, vedi `institutional_protocol_digest.md` §7 |
| `ssrn-5598690.pdf` | Parabolic SAR su BTC | **scartato** → [`NOTES_ssrn_batch.md`](../../ideas/NOTES_ssrn_batch.md) |
| `ssrn-5580590.pdf` | Multi‑agent LLM su BTC | **scartato** → stesso file |
| `ssrn-6467818.pdf` | Econometria applicata | **scartato** → stesso file |
| `MOC_ricerca.md` | Scheda **nostra**, non un ingest | Traccia di lavoro aperta. Nota prima di ripartire: il MOC imbalance è un dato **azionario** pubblicato dagli exchange USA — da verificare se e come sia ottenibile per operare su NQ |

### `mc/education/books/` — 2 fatti, 4 da fare

| Libro | Stato |
|---|---|
| Alexander Elder — *Vivere di trading* | ✅ **idee estratte** → [`NOTES_elder.md`](../../education/books/NOTES_elder.md) |
| Steve Palmquist — *Money‑Making Candlestick Patterns* | ✅ **idee estratte** → [`NOTES_palmquist_candlestick.md`](../../education/books/NOTES_palmquist_candlestick.md) |
| G. Defendi — *Strategie operative per i mercati finanziari* | ⬜ da processare |
| *Guida pratica al trading Volume 2* | ⬜ da processare |
| John T. Marino — *Trading dal divano* (2024) | ⬜ da processare |
| *Trading systems sulle curve non di prezzo* | ⬜ da processare — **il più promettente dei quattro**: è l'unico il cui titolo prometta qualcosa che non abbiamo già (equity curve trading, filtri su curve derivate) |

### Corsi in `mc/education/` — 2 fatti, 1 parziale, 3 da fare

I video restano in locale, fuori dal repo; nel repo entrano trascrizioni e note.

| Corso | Cos'è | Stato |
|---|---|---|
| `protocollo/` — **The Institutional Protocol** (Matteo Conti) | 19 trascrizioni, 11 moduli, 69 code template | ✅ **fatto ed è la fonte della pipeline** → `pipeline_prop.md` + `institutional_protocol_digest.md`. Da qui nascono tutte e sei le strategie in `mc/strategies/` |
| `morpheus/` — **Pro Trader Blueprint** | Modulo 1 «Comincia da qui» (3 tutorial), modulo 2 «I Modelli Intraday» (9 video) | ◐ **parziale**. Video 1‑5 del modulo 2: ✅ fatti (01/10) → [`ANALISI_modelli_intraday_1-5.md`](../../education/morpheus/ANALISI_modelli_intraday_1-5.md). ⬜ **Restano i video 6‑9**: *Modelli di Orderflow Puro per NQ*, *15m IVB su ES*, *5m ORB Gap Fill su ES*, *PbD su ES*. I tre su **ES** sono i più interessanti — è l'unico strumento oltre a NQ nel nostro perimetro. Il modulo 1 sono tutorial di piattaforma: nessun contenuto operativo, si salta |
| `enrico_stucchi/` — order flow / option flow | 4 PDF + 7 video | ◐ **parziale**. PDF (VolBook, Masterclass Orderflow 1‑2, Liquidity Bootcamp) → ✅ `PLAYBOOK.md` + `MOC_ricerca.md`. Trascritti i due Savius Traders Talk. ⬜ **Non trascritti i tre video Option Flow** (15/12, 08/01, 15/01). Verdetto del corso però già dato: **playbook**, non pipeline — servono dati opzioni e order flow |
| `stefano_serafini/Dax Trading Lab` | 3 lezioni (5h41) + `DAX5m.txt` + binari | ⬜ **in coda** — vedi il TODO sopra. Trascrizioni fatte, analisi del metodo MVP rimandata. Blocco strumento (Eurex non su Apex), non dati |
| `stefano_serafini/Stock Trading Lab` | 7 video (4,4 GB), metodo MVP sulle **azioni** | ⬜ da processare — ma universo azionario con stock picking: la domanda 2 della checklist lo boccia quasi certamente in partenza |
| `unger/` — **Trading System Supremacy** | 12 cartelle di strategie (BIAS, Counter Trend, DAXFirstHour, ESCounter, FXFader, Gap, IntraToOverNight, Night FIB, Stop Progressivi, Trend Following, WeeklyBump, Daily Factor) + 3 documenti | ◐ **parziale**. I **due PDF** + il `pattern base reference.docx`: ✅ fatti il 03/10 → [`NOTES_unger_pdf.md`](../../education/unger/NOTES_unger_pdf.md). ⬜ Restano le **12 cartelle di codice EasyLanguage** — ed è il blocco più grosso della coda, l'unica fonte che contenga **strategie già scritte** invece che concetti. Da guardare per prime, col filtro del rischio per trade: **ESCounter** e **Gap**; Night FIB e DAXFirstHour sono DAX, quindi Eurex, quindi fuori |

**Priorità**: la coda non è urgente. Il lavoro è portare le strategie già scritte
attraverso i gate con i dati veri; leggere altro materiale non avvicina quel risultato. Si
valuta un documento quando serve un'idea per un **buco preciso** del basket.

Aggiornamento 01/10: un buco preciso adesso c'è, ed è la ragione per cui il modulo Morpheus
è stato letto subito invece di finire in coda. ORB e VaultBreak sono morte per la stessa
causa — 95° percentile MC a ~$3.110 per micro contro un budget di $2.000 — cioè per
**rischio per trade**, non per mancanza di edge. Quindi: si legge materiale che riduca lo
stop, non materiale che aggiunga segnali. Con questo criterio, delle sei voci ⬜ qui sopra
la sola candidata seria è la libreria **Unger**, perché contiene strategie già scritte e
misurabili in mezz'ora invece che concetti da tradurre.

## Cosa cercare quando si legge qualcosa di nuovo

Le domande che hanno deciso i verdetti finora, nell'ordine in cui conviene farsele:

0. **Che asset e che costi?** Prima ancora di aprire il documento. I tre paper SSRN del
   30/09 erano tutti identificabili come fuori perimetro dal solo abstract — Bitcoin,
   rendimenti in percentuale, nessuna frizione modellata. Trenta secondi invece di un'ora.
1. **Che dati servono?** Se servono dati che non abbiamo (opzioni, MBO, L3, tick lunghi),
   il resto è accademico: `in coda` con il blocco scritto, e si va avanti.
2. **Che universo e che timeframe?** Azioni screenate su migliaia di simboli ≠ un solo
   future. Daily con hold multi‑day ≠ flat EOD obbligatorio.
3. **La metrica è convertibile nella nostra?** ROI% senza costi non si converte in avg
   trade netto in dollari.
4. **Quanto è meccanica la regola?** Se per codificarla dobbiamo inventare noi le
   definizioni (pivot, "corpo piccolo", "livello importante"), la strategia è nostra e il
   documento è solo ispirazione.
5. **Chi perde soldi contro di noi?** Se il documento non lo dice, non è una strategia.
