# Live 006 — la fase funded (29/10/2026)

**Fonti.** Trascrizione [`6._PROPFIRMS_AS_A_BUSINESS_Live_006.txt`](../../education/protocollo/transcripts/6._PROPFIRMS_AS_A_BUSINESS_Live_006.txt)
(Whisper large-v3-turbo, 58 min) e slide dal video, due versioni del PDF (18 e 20 pagine),
fotogrammi in `education/protocollo/_slide/8. Livestreaming__6. …live 006/`.

## In una riga

**Dopo l'eval cambia la domanda: non «quanto spesso passo» ma «quanti dollari di payout estraggo
da un conto funded».** Il corso la misura su Apex 50K EOD con tre strategie del Bridge, e trova
che tre insieme valgono più della migliore da sola.

## Le regole del conto funded (Apex 50K EOD PA, slide 3–4)

| | |
|---|---|
| Drawdown | $2.000 trailing EOD, toccarlo chiude il conto |
| Daily loss | $1.000, chiude la giornata, non il conto |
| Size | da 2 a 4 NQ (10 MNQ = 1 NQ), cresce con il profitto |
| Prima di ogni payout | 5 giorni da $250 o più; un giorno ≤ 50% del profitto dal payout precedente |
| Safety net | $2.100, resta sempre nel conto |
| Scala dei payout | $1.500 · 1.500 · 2.000 · 2.500 · 2.500 · 3.000 = **$13.000 massimo**, poi il conto è finito |

Servono quindi **$15.100 di profitto** (2.100 + 13.000), 30+ giorni qualificanti e 6 controlli
di consistency. Lucid è citata come buona alternativa, con un massimo estraibile più basso.

## Il test

- 4 strategie del Bridge (**DriftPullback, VWAP ADX, Overnight Bias, VaultBreak**) × 5 uscite
  (originale, R:R 0,5 · 1 · 1,5 · 2) × size da 1 a 20 MNQ.
- **Size e uscite scelte su gen 2023 → ago 2025, misura su ago 2025 → set 2026** (13 mesi).
- 20.000 conti funded simulati per risultato, giorni ripescati a blocchi di una settimana.
- Metro: **EV per conto funded** = payout medio nei primi 12 mesi, conti bruciati a $0.

## I risultati

### 1. L'uscita: l'R:R basso non vince sempre

EV per conto funded, uscita migliore di ciascuna (slide 6):

| strategia | uscita migliore | EV | size | 1° payout (mediana) |
|---|---|---|---|---|
| **DriftPullback** | originale | **$2.626** | 2 MNQ | giorno 30 |
| VWAP ADX | originale | $2.853 | 7 MNQ | giorno 28 |
| Overnight Bias | R:R 0,5 | $968 | 4 MNQ | giorno 31 |
| VaultBreak | R:R 1,5 | $1.111 | 6 MNQ | giorno 20 |

Su VWAP ADX (slide 7), più R:R vuol dire più profitto nel backtest ($79k → $86k per NQ) ma
**meno EV** ($2.853 → $787). Il punto dell'autore: il conto funded e il conto proprio sono due
problemi diversi.

**Per noi:** DriftPullback **a 2 MNQ, la nostra size live**, è la seconda strategia del test per
EV. È la conferma esterna più diretta che abbiamo finora.

### 2. La size compra velocità, non payout

VWAP ADX da sola, uscita originale (slide 8):

| MNQ | 1 | 2 | 3 | **4** | 5 | 7 | 10 | 20 |
|---|---|---|---|---|---|---|---|---|
| giorni al 1° payout | 304 | 122 | 73 | **50** | 41 | 28 | 23 | 18 |
| conti bruciati | 0% | 15% | 47% | **57%** | 68% | 75% | 82% | 82% |
| EV | $3 | $1,6k | $3,1k | **$3,9k** | $3,2k | $2,9k | $2,1k | $1,6k |

Il massimo dell'EV è a 4 MNQ, con il 57% dei conti bruciati. A 1 MNQ non si brucia niente ma
non si incassa niente: il primo payout arriva dopo più di un anno.

### 3. Tre strategie su un conto

| | EV | mediana | ≥ 1 payout anno 1 | 1° payout |
|---|---|---|---|---|
| VWAP ADX 7 MNQ da sola | $2.853 | $0 | 40% | giorno 28 |
| Overnight Bias 2 + VWAP ADX 4 | $3.735 | $0 | | |
| **Overnight Bias 1 + VWAP ADX 3 + VaultBreak 1** | **$5.590** | **$3.000** | **62%** | giorno 42 |

Le stesse tre gambe **da sole** (slide 10): Overnight Bias $173, VWAP ADX $3.055, VaultBreak
**$0**. Somma $3.228, insieme $5.590. Correlazione giornaliera 0,02–0,25; tutte e tre perdono
nel 2% dei giorni.

**DriftPullback non entra in nessuna configurazione finale.** Il perché non è detto.

### 4. Le tre configurazioni (slide 13–14 e 17–18)

| | Fast | **Balanced** (la sua scelta) | Patient |
|---|---|---|---|
| Overnight Bias (R:R 1,5) | 4 MNQ | **1 MNQ** | — |
| VWAP ADX (uscita originale) | 9–10 MNQ | **3 MNQ** | 2 MNQ |
| VaultBreak (40/75 pt) | 3–4 MNQ | **1 MNQ** | 1 MNQ |
| 1° payout (mediana) | giorno 15 | **giorno 42** | giorno 95 |
| tutti e 6 i payout | 16% | **40%** | 63% |
| mai pagati | 73% | **38%** | 20% |
| EV per conto, vita intera (anno 1) | $2.303 | **$6.223** ($5.590) | $9.122 ($3.702) |

VaultBreak nel codice ha target e stop **in dollari per posizione**: a 1 MNQ `TakeProfitDollars
80` / `StopLossDollars 150` = 40/75 pt, come la nostra [`SPEC_v8.md`](../strategies/VaultBreak/SPEC_v8.md).
A 3 MNQ vanno moltiplicati, altrimenti diventano 13/25 pt: l'autore lo segnala lui stesso.

### 5. Venti conti (il tetto di Apex)

Balanced, $329 per conto funded: anno 1 payout $179k, costo $17k, **netto $162k**; anno cattivo /
buono (1 su 10) $40k / $253k. Sul calendario reale 2024 → set 2026: netto **$446,8k**, con i
primi payout solo dal terzo trimestre e $6,6k spesi all'inizio.

## Dove il ragionamento è debole

1. **«Tre valgono il doppio di una» confronta con la size sbagliata.** VWAP ADX da sola rende di
   più a 4 MNQ ($3,9k) che a 7 ($2.853). Contro la sua size migliore il guadagno di tre strategie è
   **$5.590 / $3.900 ≈ +43%**, non 2×. Resta un guadagno, non un raddoppio.
2. **La somma delle EV da sole non è un riferimento.** L'EV non è lineare nel P&L: soglie
   ($2.100 + $1.500), scala dei payout, inattività. VaultBreak a 1 MNQ fa $0 perché non arriva mai al
   primo payout, non perché perde. Il «di più della somma» è in gran parte **size totale** (5 MNQ
   contro 3), non diversificazione.
3. **Uscite e size scelte fra 5 × 20 combinazioni per strategia** sul periodo 2023–ago 2025. La
   finestra di misura di 13 mesi è l'unica pulita. Per Overnight Bias la nota a piè della slide 14
   dice che **con l'R:R 3 originale il book faceva lo stesso** (EV $5.803 contro $5.590): l'1,5 non è
   una scoperta.
4. **«Solo dati fuori campione dal 2023» non vale per VWAP ADX:** il gate ADX è stato pubblicato il
   3/7/2026, dopo aver visto le performance recenti (Live 002). La finestra di misura ago 2025 →
   set 2026 è in gran parte in-sample per il gate.
5. **Le tabelle 2024–26 «in ordine reale» sono quasi tutte in-sample:** le size sono scelte su
   gen 2023 → ago 2025.
6. **Venti conti con gli stessi segnali sono un solo conto ripetuto venti volte.** Un trimestre
   cattivo li colpisce tutti. Il calendario reale (Q1 2024 −$6,6k, Q2 e Q3 2025 a zero) lo mostra
   meglio delle medie annue.
7. **Non modellato:** Apex che sposta il conto su live prima del sesto payout, tempi di
   pagamento. I «10 segnali opposti» l'autore stesso dice che sono probabilmente sbagliati (28:58).

## Cosa cambia per noi

| | decisione |
|---|---|
| **Gate marginale** | **Resta sul pass rate dell'eval.** Siamo in eval su Lucid. La domanda funded viene dopo il primo pass. |
| **Fase funded** | Quando passiamo: un simulatore dei payout **con le regole funded di LucidFlex**, non di Apex. Metro = EV per conto, conti bruciati a $0. Da scrivere e pre-registrare **prima** del pass, non dopo. |
| **Overnight Bias** | La SPEC resta su **R:R 3** (default del codice, k = 1). L'1,5 del corso è scelto su 5 uscite, e la sua stessa nota dice che il 3 fa uguale. |
| **VaultBreak v8** | Confermato: 40/75 pt per contratto. La SPEC è giusta. |
| **VWAP ADX** | Contaminazione confermata: la SPEC già la tratta così. |
| **DriftPullback** | EV $2.626 a 2 MNQ sul suo test. Non toccarla. |

**Altre cose dette:**
- La prossima live è solo domande e risposte.
- L'autore spinge IQ Capital: overnight permesso e automazione permessa, ma ancora senza
  connessione a MultiCharts.
