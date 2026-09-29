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
| 2026‑09‑28 | [Alexander Elder — *Trading for a Living* (1993)](../education/books/NOTES_elder.md) | Classico discretionary: psicologia, analisi grafica, indicatori, Triple Screen, money management | **idee estratte** | Variante d'ingresso `EntryMode 1` di DriftPullback (stop oltre l'estremo del pullback, dal Triple Screen). Force Index / Elder‑Ray annotati come candidati filtro Stage 4. **Scartate le divergenze** (si definiscono a posteriori). |
| 2026‑09‑28 | [Steve Palmquist — *Money‑Making Candlestick Patterns* (2008)](../education/books/NOTES_palmquist_candlestick.md) | Pattern a candele **backtestati**, azioni USA daily | **idee estratte** | Variante `TriggerMode 1` di DriftPullback (barra di pullback con rifiuto). I pattern in sé non trasferiscono: universo azionario con selezione cross‑sectional, daily multi‑day contro il nostro flat EOD, metrica in ROI% senza costi. |
| 2026‑09‑29 | `mc/ideas/Class summary Freddy 19.05.pdf` | Sintesi di una lezione su **GEX / GEXBot**: gamma exposure, livelli di open interest su NDX/SPX/QQQ, lettura con tape e delta | **in coda** | **Blocco dati**: richiede flusso opzioni e livelli di gamma, che non sono nel feed futures TradeStation né in dxFeed CME. Impianto dichiaratamente discrezionale ("livello prima, reazione poi, ingresso per ultimo") → anche con i dati servirebbe una riscrittura meccanica completa. Prima lettura, valutazione piena non fatta. |
| 2026‑09‑29 | `mc/ideas/…Liquidity_Gate_Complete_Academic_Specification_v5.0.docx` | Paper (Westbrook, lug 2026): classifica l'ambiente di liquidità su NQ in 5 tier per decidere quando il flusso istituzionale può forzare l'hedging dei dealer | **in coda** | **Blocco dati**: i criteri sono profondità del book a riposo, velocità di replenishment, gap nel book e **identificatori Market‑by‑Order** — cioè L3/MBO. Vedi `institutional_protocol_digest.md` §7: serve il Bridge (chiuso) + un'entitlement MBO separata, e resta aperto il problema della simmetria storico/live. Prima lettura, valutazione piena non fatta. |

## Da valutare (ingeriti, non ancora letti)

Una riga anche qui: sapere **cos'è** un documento senza averlo letto costa trenta secondi
e evita di riaprirlo per scoprire che non serve.

**`mc/ideas/`**
- `ssrn-5580590.pdf` — *An Adaptive Multi‑Agent Bitcoin Trading System* (Singhi, UCL), 19 pp.
  LLM per alpha generation e gestione di portafoglio su crypto. Fuori dal nostro perimetro
  (futures, PowerLanguage, prop): da leggere semmai per il metodo, non per la strategia.
- `ssrn-5598690.pdf` — *Evaluating the Parabolic SAR Strategy on Bitcoin* (Mesíček), 16 pp.
  Valutazione di un singolo indicatore su BTC.
- `ssrn-6467818.pdf` — 59 pp. di econometria delle serie storiche finanziarie: stazionarietà
  (ADF), volatility clustering, stylised facts, modelli previsivi. **Metodologia, non
  strategie** — il candidato più utile dei tre se serve uno strumento statistico.
- `MOC_ricerca.md` — scheda di ricerca **nostra** (non un ingest): MOC imbalance e ultimi
  10 minuti, da materiale Stucchi. Ha già una traccia di lavoro dentro. Nota prima di
  ripartire: il MOC imbalance è un dato **azionario** pubblicato dagli exchange USA, da
  verificare se e come sia ottenibile per operare su NQ.

**`mc/education/books/`**
- `G. Defendi - Strategie operative per i mercati finanziari.pdf`
- `Guida pratica al trading Volume 2.pdf`
- `John T. Marino – Trading dal divano (2024).pdf`
- `Trading systems sulle curve non di prezzo.pdf`

**Corsi** (video esclusi dal repo, restano in locale)
- `mc/education/enrico_stucchi/` — order flow e option flow; ha già un `PLAYBOOK.md` e
  `MOC_ricerca.md` derivati.
- `mc/education/stefano_serafini/` — Dax Trading Lab. Contiene **codice**: `DAX5m.txt` e
  due file di strategia esportati (`.ELD`, `.sef`). Da guardare prima delle altre cartelle:
  è materiale eseguibile, non solo video.
- `mc/education/morpheus/` — Pro Trader Blueprint.
- `mc/education/unger/` — Trading System Supremacy (cartelle già montate come working dir).

**Priorità**: la coda non è urgente. Adesso il lavoro è portare sei strategie già scritte
attraverso i gate con i dati veri; leggere altro materiale non avvicina quel risultato.
Si valuta un documento quando serve un'idea per un buco preciso del basket (oggi: nessuno
— mancano i test, non le idee).

## Cosa cercare quando si legge qualcosa di nuovo

Le domande che hanno deciso i verdetti finora, nell'ordine in cui conviene farsele:

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
