# SPEC — Trend Following di Unger, su 6E, GC, ES, NQ (Stage 0)

**Ipotesi**: dopo un giorno di indecisione (corpo sotto metà del range), la rottura del
massimo o del minimo della giornata in corso, durante la mattina europea, avvia un
movimento che continua. È un breakout da compressione di volatilità.
**Perché**: un giorno di indecisione lascia ordini accumulati ai bordi del range; quando
la liquidità europea arriva e li rompe, chi era posizionato contro deve uscire e alimenta il
movimento. Chi perde: chi vende i massimi / compra i minimi aspettandosi un altro giorno
laterale.
**Fonte**: Andrea Unger, *Trading System Supremacy*, modulo 4 (4x01–4x04), editor del
20/01/2016. **EURUSD forex 15 min**, dati TradeStation, grafico in ora di New York,
2008 → gennaio 2016. Due versioni finali:

| | versione | parametri sul grafico | codice | risultato mostrato |
|---|---|---|---|---|
| **A** | `DevelopFineTune` (4x03, multi‑day) | `(6, 4, 18, 19, 400, 1330, 1200, 1100, 0.011, 0.035, 0, 0)` | 4x03 al 9:50 | equity da $100.000 a ~$245.000, piatta 2013–2015 |
| **B** | `DevelopID` (4x04, intraday) | `(1, 1, 35, 35, 300, 500, 1200, 1100, 0.0075, 0.025)` | 4x04 allo 0:40 | 539 trade, WR 52,9%, avg $114, vinc. $613 / perd. $446, su 100.000 € |

Costi nei test di Unger: non visibili. Trascrizioni fedeli: `UngerTF.txt`, `UngerTF_ID.txt`.
Codici per i futures: `UngerTF_A.txt`, `UngerTF_B.txt`.

## Regole

| | A (multi‑day) | B (intraday) |
|---|---|---|
| Finestra (ora di New York) | barre fra 04:00 e 13:30 | barre fra 03:00 e 05:00 |
| Filtro sul giorno | ieri indecisione (pattern 1: corpo < 50% del range) | — |
| Long | (pattern 6 o 39) e non 18 → buy stop al **massimo di oggi** | pattern 1 e non 35 → buy stop al **massimo di oggi** |
| Short | (pattern 4 o 39) e non 19 → sell stop al **minimo di oggi** | pattern 1 e non 35 → sell stop al **minimo di oggi** |
| Stop / target su EURUSD | 110 / 350 pip | 75 / 250 pip |
| Uscita | stop, target o inversione, anche dopo giorni | stop, target o **fine sessione** |

Pattern: 1 = ieri corpo < 50% del range; 4 / 6 = oggi l'escursione sopra / sotto l'apertura
supera quella di ieri; 18 / 19 = ieri chiusura in calo / in rialzo di oltre lo 0,5%; 35 = oggi
inside rispetto a ieri; 39 = ieri non outside bar. In A il pattern 39 è vero quasi sempre, quindi
6 e 4 contano poco: il filtro vero è "ieri indecisione, e ieri non un giorno direzionale forte
contro".

## Strumenti

| strumento | ruolo | orari (fuso dell'exchange) | stop / target A | stop / target B |
|---|---|---|---|---|
| **6E** (`@EC`) | **replica**: lo strumento di Unger, dati che non ha visto | Chicago: A 300–1230, B 200–400 | 0,011 / 0,035 (= Unger) | 0,0075 / 0,025 (= Unger) |
| **GC** → MGC | porting: l'oro ha Londra come piazza principale | New York: A 400–1330, B 300–500 | 0,83% / 2,6% | 0,56% / 1,9% |
| **ES** → MES | porting | Chicago, come 6E | 0,83% / 2,6% | 0,56% / 1,9% |
| **NQ** → MNQ | porting | Chicago, come 6E | 0,83% / 2,6% | 0,56% / 1,9% |

**Stop in percentuale, regola unica senza ottimizzazione** (come nel Counter Trend): l'EURUSD
2008–2015 ha una media di ~1,33, quindi 0,011 = 0,83%, 0,035 = 2,6%, 0,0075 = 0,56%,
0,025 = 1,9%. Su 6E si usano i valori di Unger in prezzo, così com'erano.

| | stop A | stop B |
|---|---|---|
| 6E (125.000 €) | **$1.375 a contratto** | **$938 a contratto** |
| MGC (oro ~4.100) | ~$340 | ~$230 |
| MES (ES ~7.800) | ~$325 | ~$220 |
| MNQ (NQ ~25.000) | ~$415 | ~$280 |

**6E è causa B per costruzione** su LucidFlex 50k: niente micro, uno stop vale da metà a due
terzi dell'MLL. Si testa per sapere **se l'edge di Unger esiste fuori campione** sul suo
strumento: se c'è su 6E e non sugli altri, la strategia va in cimitero con causa B, non A.

**Giornata.** Su 6E la sessione CME parte alle 17:00 CT (18:00 New York), un'ora dopo il forex
spot su cui Unger calcola massimo, minimo e pattern del giorno. Si accetta lo spostamento.

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi. Tutto dopo gennaio 2016 è fuori
campione per l'autore.

## Varianti pre‑registrate
- **A** = `DevelopFineTune`, multi‑day: va contro "flat prima della chiusura" e attraversa i
  weekend; vale come misura dell'edge.
- **B** = `DevelopID`, intraday: **caso base per la prop**.

## Rischi dichiarati prima dei run
- **Profilo fuori dalla pipeline per costruzione.** Target 3,3 volte lo stop: i numeri di Unger
  su B danno WR 52,9% e R:R 1,37, cioè **falliscono già WR ≥ 55% e R:R 0,5–1**. Il run misura
  l'edge (t e avg); se l'edge c'è e fallisce solo sul profilo, si scrive così, non "edge assente".
- **Test multipli.** 4 strumenti × 2 varianti = 8 run nell'IS. Il massimo atteso del t di 8
  estrazioni casuali è ~1,4: un solo run appena sopra 2 non basta, serve coerenza (stesso
  segno su A e B, o su più strumenti).
- **Orario.** 03:00–05:00 New York è la notte per gli indici USA: su ES e NQ l'ipotesi "mattina
  europea" regge meno che su GC e 6E.

## Worst day strutturale
- **B**: nessun limite di ingressi nella finestra; in pratica uno stop e un rientro: **2 stop**
  ≈ $460 per MGC, $440 per MES, $560 per MNQ, più costi.
- **A**: non limitato (posizioni di più giorni, gap del weekend).

## Soglie del Gate 2 (LucidFlex 50k; ÷10 per i micro)

| | 6E | GC | ES | NQ |
|---|---|---|---|---|
| avg trade netto | ≥ $85 | ≥ $140 | ≥ $140 | ≥ $70 |
| max DD sul contratto pieno | ≤ $2.000 (nessun micro) | ≤ $10.000 | ≤ $10.000 | ≤ $10.000 |
| peggior trade sul contratto pieno | ≤ $500 | ≤ $5.000 | ≤ $5.000 | ≤ $5.000 |
| n, PF, WR, R:R, annuale | come pipeline: ≥ 200, ≥ 1,2, ≥ 55%, 0,5–1, nessun anno > 50% | | | |

**Costi** per lato, slippage incluso, campo slippage a 0: 6E **8.65$**, GC **12.5$**, ES
**15$**, NQ **7.5$** per Contract.

**Kill**: gate della pipeline su **B**, strumento per strumento. Kill generale se A e B hanno
avg netto ≤ 0 su tutti e quattro.
