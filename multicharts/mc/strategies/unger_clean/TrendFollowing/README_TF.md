# Trend Following di Unger (6E, GC, ES, NQ) — istruzioni

Codice unico: **`UngerTF.txt`** → salva come **`Mario_UngerTF`** (signal); input **`Versione`**
0 = A (multi‑day), 1 = B (intraday). Richiede la funzione **`Mario_PtnBaseSA`**. Spec: `SPEC.md`.

## Chart
- **15 min**, data source TradeStation, timezone **Exchange**, Bar Magnifier **1 min ON**,
  Backtesting Mode Classic, Max bars back 50.
- **@EC, @ES, @NQ**: exchange Chicago, template **"CME Globex 17-16 no break"**.
- **@GC**: exchange New York, template **"COMEX Globex 18-17 no break"**.
- Costi per contratto, slippage `0 ticks`: @EC `8.65$`, @GC `12.5$`, @ES `15$`, @NQ `7.5$`.

## Input per strumento
Gli input a 0 prendono il default della versione (orari di Chicago, stop e target di Unger in
prezzo). Si cambia solo questo:

| | A (`Versione 0`) | B (`Versione 1`) |
|---|---|---|
| @EC | niente | niente |
| @ES, @NQ | `StopPct 0.83`, `ProfitPct 2.6` | `StopPct 0.56`, `ProfitPct 1.9` |
| @GC | `MyStartTrade 400`, `MyEndTrade 1330`, `StopPct 0.83`, `ProfitPct 2.6` | `MyStartTrade 300`, `MyEndTrade 500`, `StopPct 0.56`, `ProfitPct 1.9` |

Controlla gli input in *Format Signals* prima di ogni run: ricompilare non aggiorna quelli di
una strategia già sul grafico.

## Stage 1 — meccanica, ~100 giorni

| run | chart | size | file in `reports/` | |
|---|---|---|---|---|
| A | @EC | 1 | `TF_S1_EC_A_x1.xlsx` + log (`ShowLog 1`) | ✅ 29/10 |
| A10 | @EC | 10 | `TF_S1_EC_A_x10.xlsx` | ✅ 29/10 |
| B (`Versione 1`) | @EC | 1 | `TF_S1_EC_B_x1.xlsx` + log | ✅ 29/10 |
| B (`Versione 1`) | @GC (input di GC) | 1 | `TF_S1_GC_B_x1.xlsx` + log | ✅ 24/10 |

### Controlli (Gate 1)
1. **Finestra**: in A gli ingressi cadono fra le 03:15 e le 12:30 CT (GC: un'ora dopo, NY), in
   B fra le 02:15 e le 04:00 CT (GC 03:15–05:00 NY). Mai di domenica.
2. **Livelli**: `entry` = `hiD` (long) o `loD` (short) del momento, o peggio se il prezzo salta.
3. **Filtri**: in A nessun ingresso dopo un giorno con corpo ≥ 50% del range; in B nessun
   ingresso con la giornata ancora inside rispetto a ieri (li ricontrollo io con i dati).
4. **Stop / target**: @EC A $1.375 / $4.375, B $937,50 / $3.125 a contratto; GC in % del
   prezzo d'entrata (`stop$` e `tgt$` nel log).
5. **Uscite**: A tiene anche overnight e si gira sul segnale opposto; B è flat a fine sessione
   (16:00 CT, 17:00 NY su GC).
6. **Scala ×10**: A10 = 10 × A.

## Stage 2 — IS 2020‑01‑01 → 2024‑12‑31, 1 contratto, senza log
A e B su @EC, @GC, @ES, @NQ: 8 run, file `TF_S2_<EC|GC|ES|NQ>_<A|B>_IS.xlsx`.
`ShowLog 0`, input della tabella sopra, template e costi dello strumento (@GC **12.5$**, non
8.65$). Il grafico deve partire almeno da metà dicembre 2019: i pattern guardano fino a 5
sessioni indietro.

## Note dello Stage 1
**Run A su @EC (24/10/2026)**: 38 trade in 114 giorni, report `TF_S1_EC_A_x1.xlsx`, log
`TF_S1_EC_A_log.txt`.
- Ingressi fra le 03:30 e le 12:14 CT, in 21 giornate su ~80: dentro la finestra.
- Ingresso a `hiD` / `loD` del momento (il log stampa i valori a fine barra, quando il
  massimo può essere già salito oltre l'entrata).
- Stop $1.375 e target $4.375 a contratto, come da spec. In 114 giorni **non scatta né lo stop
  né il target**: tutte le uscite sono inversioni, perché il livello opposto (il minimo o il
  massimo del giorno) è quasi sempre più vicino di 110 pip. È la meccanica di Unger.
- **Inversioni a raffica nei giorni laterali**: il 28/08 sette trade in sei ore, con perdite
  da $110 a $225 ciascuno. Previsto dal codice (i due stop d'ingresso restano attivi tutta la
  finestra), ed è il costo principale della versione A.
- Il filtro del pattern 1 non si può ricontrollare qui (nessun dato di 6E in quantlake); la
  funzione `Mario_PtnBaseSA` è già verificata (Gate 1 del 18/10).

**Run B su @EC (24/10/2026) — invalido, e con lui il run A.** 20 trade, ingressi fra le 02:29
e le 03:59 CT (giusto), stop $937,50 / target $3.125 (giusto), un ingresso al giorno. Ma
l'uscita di fine sessione arriva alle **23:59**, e solo il venerdì alle 15:59: il chart di @EC
ha un template **a giorno di calendario** (00:00–23:59), probabilmente quello rimasto da FX Fix,
non il "CME Globex 17-16 no break". Conseguenze:
- in B la posizione resta aperta 8 ore oltre la chiusura delle 16:00, attraverso la pausa;
- in A e in B il massimo e il minimo "di oggi" partono da mezzanotte invece che dalle 17:00
  del giorno prima, e i pattern di "ieri" leggono il giorno di calendario.
Da rifare A e B su @EC con il template 17-16. Il run B è stato fatto con il vecchio
`Mario_UngerTF_B` (log `TFB`), con la stessa logica di `Versione 1`.

**Run B su @GC (24/10/2026) — meccanica giusta.** 19 trade in 130 giorni, report
`TF_S1_GC_B_x1.xlsx`, log `TF_S1_GC_B_log.txt` (tolte due righe di un primo giro con
`StopPts 0.56` al posto di `StopPct`).
- Ingressi fra le 03:30 e le 04:44 di New York, uno al giorno; dopo uno stop nessun rientro,
  perché la finestra è già chiusa.
- Stop allo **0,56% del prezzo d'entrata** (es. 4.413,80 → $2.471,73, uscita 24,8 punti sotto) e
  target all'1,9%: mai toccato, le vincenti escono a fine sessione.
- Uscita di fine sessione alle **17:00** NY (template 18-17 giusto); il 19/06 alle 12:59, chiusura
  anticipata per Juneteenth.
- **Commissione impostata a 8.65$** (quella di @EC) invece di 12.5$: non cambia la meccanica, ma
  nello Stage 2 su GC va 12.5$.

**Run B su @EC, secondo giro (24/10/2026) — template giusto, input sbagliati.** Le uscite di fine
sessione ora sono alle 15:59 CT (31 su 32): il template 17-16 è a posto. Ma sul grafico sono
rimasti gli input di GC: `MyStartTrade 300` / `MyEndTrade 500` (ingressi 03:30–05:00 CT, un'ora
dopo la finestra di Unger) e `StopPct 0.56` / `ProfitPct 1.9` (stop ~$810 invece dei $937,50
fissi). Report non conservato. Da rifare con tutti gli input a 0 tranne `Versione 1`.

**Run B su @EC, terzo giro (29/10/2026) — meccanica giusta.** `Mario_UngerTF`, `Versione 1`,
input a 0, template 17-16 ricreato. 33 trade in 135 giorni, report `TF_S1_EC_B_x1.xlsx`, log
`TF_S1_EC_B_log.txt`.
- Ingressi fra le 02:29 e le 03:59 CT, dentro la finestra 02:00–04:00.
- Stop $937,50 e target $3.125 a contratto (i valori di Unger): non scattano mai in 135 giorni.
- Uscite: 31 a fine sessione alle **15:59 CT**, tutti i giorni; 2 inversioni nella finestra
  (20/07 e 23/09: il prezzo rompe prima un lato e poi l'altro), come da codice.
- Numeri (WR 66,7%, t 2,34 su 33 trade) solo informativi: lo Stage 1 non giudica l'edge.

**Run A e A10 su @EC (29/10/2026) — meccanica giusta. Gate 1 passato.** Template 17-16,
`Versione 0`, input a 0. 55 trade in 134 giorni (sostituiscono il run A del 24/10, fatto con il
template a giorno di calendario).
- Ingressi fra le 03:30 e le 12:14 CT, dentro la finestra 03:00–12:30.
- 53 uscite per inversione, 1 stop (29–30/07: 1,1453 → 1,1563, 110 pip = $1.375), 1 aperta.
- **A10 = 10 × A** su 54 trade su 55; l'unica differenza è il trade ancora aperto, valutato a un
  prezzo diverso perché i due run sono stati lanciati in momenti diversi.
- Inversioni a raffica nei giorni laterali (25/06, 07/07, 28/08), come nel giro del 24/10.

## Stage 1 — esito
**Gate 1 passato** (29/10/2026) su @EC (A, A10, B) e @GC (B). Prossimo: Stage 2.

## Stage 2 — risultati
**@EC (29/10/2026) — A senza edge; B con edge al limite, causa B per costruzione.** Report `TF_S2_EC_A_IS_x10.xlsx` e
`TF_S2_EC_B_IS_x10.xlsx`: 2020-01-06 → 2024-12-31, template 17-16, 8.65$, ma **a 10 contratti**
(Strategy Properties rimasta dal run A10). Il t non dipende dalla size; i numeri sotto sono per
contratto.

| run | n | avg/contratto | t | WR | R:R | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 663 | −$28 | −0,84 | 33,2% | 1,83 | +9.568 | −3.831 | −6.508 | −5.824 | −11.998 |
| B | 378 | +$51 | 1,98 | 52,4% | 1,19 | +2.592 | +3.184 | +9.121 | +7.572 | −3.102 |

- **A**: le 624 inversioni fanno zero netto (−$889 in tutto); il risultato è 6 target (+$26.146)
  contro 32 stop (−$44.554). Ingressi su tutta la finestra 03:00–12:30, un terzo fra le 03 e le 04.
- **B**: tutto l'utile viene dalle 311 uscite a fine sessione (+$50.063, $161 l'una); 20 stop
  (−$19.096) e 47 inversioni (−$11.601) se ne mangiano più di metà. Il WR (52,4%) replica quello
  di Unger (52,9%). t 1,98 contro la soglia di 2 è varianza (p ≈ 0,05 a due code), e sopra il
  massimo atteso per caso su 8 run (~1,4): **l'edge di Unger fuori campione c'è, al limite**.
  L'avg ($51 contro $85) e il WR/R:R mancano, ma il WR e l'R:R erano fuori profilo per
  costruzione (SPEC) e 6E era già causa B per costruzione (stop $938, niente micro). Unico
  segnale contrario: il 2024 negativo.
- Come da SPEC, 6E serviva a sapere se l'edge esiste fuori campione: **sì per B**. 6E non si
  trada (causa B); la domanda passa a @GC, @ES, @NQ: se l'edge non si trasferisce, la strategia
  va in cimitero con causa B, non A.

**@GC, @ES, @NQ (29/10/2026).** 1 contratto, IS completo, meccanica controllata dalla List of
Trades: finestre d'ingresso giuste (GC A 04–13 NY, B 03–05 NY; ES/NQ A 03–12 CT, B 02–03 CT),
uscite di fine sessione alle 17:00 NY su GC e alle 15:59 CT su ES/NQ (12:00 nei giorni corti).
Nei file di MC i nomi erano invertiti su GC e NQ (`Mario_UngerTF` = B); qui sono rinominati.
**@NQ girato senza commissione** (`7.50$ per Contract [Fixed 0$ per Contract]`: il P&L è punti ×
20 esatti): i numeri sotto sono corretti a mano con −$15 a trade, file `_comm0`.

| run | n | avg | t | WR | peggiore/micro | DD/micro | anni negativi |
|---|---|---|---|---|---|---|---|
| GC A | 755 | +$79 | 0,95 | 32,1% | $264 | $7.338 | 2021, 2024 |
| GC B | 318 | −$12 | −0,16 | 41,8% | $178 | $3.402 | 2021, 2023, 2024 |
| ES A | 716 | +$33 | 0,39 | 31,7% | $276 | $5.788 | 2023, 2024 |
| ES B | 333 | +$42 | 0,52 | 40,5% | $184 | $2.572 | 2021, 2024 |
| NQ A | 767 | +$175 | 1,31 | 29,3% | $402 | $5.761 | nessuno |
| **NQ B** | 243 | **+$285** | **1,73** | 39,9% | $264 | $2.386 | **nessuno** |

Verdetto, con la B che decide strumento per strumento:
- **via A** (t ≥ 2, WR ≥ 55%, R:R 0,5–1): nessuno, come previsto dal profilo.
- **via B** (t > 0,5, peggiore ≤ $500 per micro): **NQ B passa** (t 1,73, cinque anni su
  cinque positivi); **ES B passa al filo** (t 0,52, 2024 −$17.645: compatibile col caso);
  **GC B no** (t −0,16): GC in cimitero, causa A.
- Il WR della B su questi strumenti (40%) non è quello di Unger su 6E (52%): la B tiene il
  target al 1,9% e vince a fine sessione meno spesso.
- Kill generale non scattato (A e B positive su NQ ed ES).

Prossimo: il gate marginale (`pipeline_semplice.md`, fase 3b), un OOS 2025-2026 per candidata.
