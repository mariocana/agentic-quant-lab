# SPEC — Serafini LAP, ES (Stage 0, 03/11/2026)

**Fonte:** Stefano Serafini, corso «S&P Trading Lab», Swiss Capital School, **Lezione 2 del
15/10/2026** (`2. Master S&P 500 - Lezione 2 - 15 ottobre 2026.pdf`, slide 10-19; contesto
alle slide 39-43 e 55). La regola è dell'autore, alla lettera. Il codice non c'è: l'autore
mostra solo regola, curva e performance summary di TradeStation. Le letture dove la slide è
ambigua sono scritte sotto, **prima** di qualsiasi run.
**Codice:** `SerafiniLAP.txt` (da scrivere dopo il commit di questa SPEC).

## Ipotesi

Quando il cash apre **dentro il range di ieri** ma staccato dalla chiusura di ieri di almeno lo
0,1%, il prezzo tende a tornare verso quella chiusura. Si fada l'apertura: short se ha aperto
sopra la chiusura, long se ha aperto sotto, target sulla richiusura con un tetto dello 0,2%,
stop dello 0,3%.

## Perché dovrebbe funzionare

- **La chiusura di ieri è un riferimento vero, non una riga sul grafico.** Alle 15:00 CT
  chiude il cash (asta di chiusura delle azioni) e si fissa il **settlement** di ES. È il
  prezzo su cui sono marcati book, margini e opzioni. L'autore: «si tende spesso a tornare
  sulla chiusura precedente come riferimento» (slide 39), «soprattutto nei primi 15-30 min»
  (slide 11).
- **Un'apertura dentro il range di ieri non porta un prezzo nuovo.** Sta in una zona dove il
  mercato ha già scambiato ieri, e lo stacco dalla chiusura è più facilmente sbilanciamento
  degli ordini d'apertura (MOO, posizionamento overnight) che informazione. La prima ora e
  mezza del cash è mean reverting e lì i breakout non funzionano (slide 39-43).
- **Il filtro toglie proprio i gap che partono in trend.** «Un gap molto spesso è l'inizio di
  un trend ... entro 1 dev. st. è normale richiudere» (slide 19). Un'apertura fuori dal range
  di ieri è il caso più vicino a «oltre il normale», e la regola la esclude.

**Chi perde:** chi insegue l'apertura nel verso dello stacco (ordini d'apertura, breakout nella
price discovery) e paga un prezzo che il mercato non accetta; noi forniamo la liquidità
contraria e incassiamo il ritorno verso il settlement.

## È un parente stretto di ON Reversal, e va detto

ON Reversal (YM) fadava il movimento della notte verso la chiusura RTH di ieri, sulla stessa
finestra (apertura cash) e nello stesso verso. **È la stessa famiglia**, ed è morta nell'IS.
GoldGapper (gap d'apertura sull'oro) idem, VWAP Fade (fade di una deviazione intraday) idem.
Le differenze del LAP sono tre, e solo la prima è di sostanza:

1. **Solo aperture dentro il range di ieri.** ON Reversal entrava su ogni stacco abbastanza
   grande, compresi i gap fuori dal range. Se le perdite di quella famiglia stanno nei gap
   fuori dal range (i giorni di trend della slide 19), il LAP le toglie per costruzione:
   **è questa l'ipotesi che il test separa**.
2. **Bracket fisso in percentuale con target corto** (al massimo la richiusura, al massimo lo
   0,2%), invece di target e stop proporzionali allo stacco. Cambia il profilo (WR alto,
   R:R ~0,6), non il meccanismo.
3. **ES invece di YM.** Non è una differenza: i quattro indici USA sono correlati 0,8-0,95
   intraday (`pipeline_semplice.md`).

**Conseguenza dichiarata.** Se il LAP muore, conferma che il fade dell'apertura verso la
chiusura di ieri non ha edge sugli indici USA 2020-24 neanche filtrato per range: la famiglia
si chiude e non si riapre con un altro filtro. Se passa, l'edge è nel filtro dentro il range
e lo si scrive così.

## Regole

| | |
|---|---|
| Famiglia | mean reversion all'apertura · fade dello stacco verso la chiusura di ieri (gap fill), long e short |
| Strumento · TF · sessione | `@ES` → **MES** per LucidFlex 50k · **1 min** · sessione **CME RTH 08:30-15:15 CT**, timezone Exchange · **data2 `$SPX.X` 1 min** (solo per la scala delle percentuali, vedi sotto) |
| Livelli di ieri | `C1` = close della barra delle **15:00 CT** di ieri · `H1` / `L1` = massimo e minimo di ieri **08:30-15:00 CT** (barre 08:31 → 15:00). Tutti su `@ES` |
| Scala % | `P` = chiusura di ieri di `$SPX.X` (15:00 CT). Le tre percentuali si calcolano su `P`, non sul prezzo di `@ES` |
| Apertura | `O` = open della prima barra RTH di oggi (barra delle 08:31, primo scambio dopo le 08:30:00) |
| Armamento | **lap up**: `O ≥ C1 + 0,001·P` **e** `O < H1` → short · **lap down**: `O ≤ C1 − 0,001·P` **e** `O > L1` → long |
| Annullamento | se la barra delle 08:31 ha già toccato `C1` (lap up: `Low ≤ C1`; lap down: `High ≥ C1`), il lap si è richiuso prima che si possa entrare: niente trade |
| Trigger | alla chiusura della barra delle 08:31 → **next bar at market** (fill all'apertura della barra delle 08:32, in MultiCharts timbrato 08:32) |
| Stop | `S = 0,003·P` arrotondato al tick (0,25), dal **prezzo di fill** |
| Target | il **più vicino** fra `C1` e `fill ∓ T`, con `T = 0,002·P` arrotondato al tick. Short: `max(C1, fill − T)` · long: `min(C1, fill + T)`. Se il fill è già oltre il target, si esce alla barra dopo |
| Altre uscite | **flat alle 15:00 CT**: uscita a mercato emessa alla chiusura della barra delle 14:59, fill all'apertura di quella delle 15:00. `SetExitOnClose` come rete per le giornate corte |
| Guardrail | **1 trade al giorno**, una posizione alla volta. **Lo stop copre anche la barra d'ingresso** (è il minuto più volatile della giornata). Il target sulla `C1` può partire dalla barra dopo, se la piattaforma non permette altro: un tocco del target nel minuto d'ingresso non preso è conservativo, e la checklist lo annota |
| Trade/giorno | 0-1. L'autore ne ha 1.868 su ~20 anni, ~37% dei giorni: **~93 l'anno, ~450-500 nell'IS** |
| Profilo atteso | WR 62-66%, R:R realizzato 0,55-0,65 (sotto lo 0,67 nominale: target spesso sulla richiusura, più corto dello 0,2%) |

**IS:** `2020-01-01 → 2024-12-31` · **OOS:** `2025-01-01 → oggi`, una volta sola.
**Forward pulito:** dal `15/10/2026` (vedi Contaminazione).

## Le letture, scritte prima del run

Tre punti in cui la slide non basta. Per ciascuno c'è una scelta e il perché. **I primi due
sono da confermare con Mario prima dello Stage 1**: se ne cambia uno prima di qualsiasi run, si
riscrive la SPEC e k resta 1; dopo il primo run, ogni cambio è una variante (k + 1).

### 1. Il target: il più vicino fra la chiusura di ieri e lo 0,2%

La slide 15 (e la 16) scrive due righe di seguito: `TARGET = 0.2% (14 punti)` e
`TARGET = Chiusura di ieri`. La lettura scelta è **il più vicino dei due**:

- è l'**unica in cui sono vere entrambe le righe**: non si va mai oltre la chiusura (la tesi
  è la richiusura, «si punta alla richiusura sulla chiusura precedente») e non si chiede mai
  più dello 0,2%;
- **il performance summary dell'autore la sostiene.** Il trade vincente più grande è
  **$787,50 = 15,75 punti di ES**, cioè esattamente lo 0,2% di 7.875, il livello di ES
  dell'ottobre 2026 (slide 13: EPZ26 intorno a 7.740-7.860). Con il target sulla sola chiusura,
  senza tetto, un lap dello 0,5% richiuso nel 2025-26 varrebbe 30-40 punti ($1.500-2.000):
  il massimo sarebbe molto sopra $787,50. Quindi il tetto dello 0,2% c'è;
- fra «tetto 0,2%» e «0,2% fisso, ignorando la chiusura», la seconda lettura butta via la
  riga `TARGET = Chiusura di ieri` e su un lap fra lo 0,1% e lo 0,2% metterebbe il target
  **oltre** la chiusura, contro la tesi. La vincita media dell'autore ($306, ~6,1 punti) e il
  rapporto vincita/perdita 0,58 (sotto lo 0,67 nominale) vanno nella stessa direzione: vincite
  più corte dello 0,2% pieno. Non è una prova (il summary mescola vent'anni di prezzi e le
  uscite di fine giornata), è coerenza.

### 2. «Ieri»: la sessione cash 08:30-15:00 CT, per tutti e tre i livelli

- **Chiusura `C1` alle 15:00 CT**, come fissato con Mario e come la slide 10 («chiusura della
  sessione cash precedente: ore 15 Chicago, asta chiusura»). È anche l'ora del settlement di ES:
  è il riferimento strutturale più forte che c'è.
- **Massimo e minimo sulla stessa finestra, 08:30-15:00 CT.** La slide 10 dice «di tutta la
  sessione», ma la regola nasce sul future nel cash (slide 13, «Partiamo dal Future nel Cash
  8.30-15.15»), il disegno della slide 14 usa candele giornaliere che aprono all'apertura del
  cash, e la curva dell'autore è su **`@ES.D` 1 min**, la serie della sola sessione diurna, dove
  il massimo e il minimo di ieri non vedono la notte. Stessa finestra della chiusura: un solo
  «ieri».
- **Da confermare con Mario.** L'autore ha due differenze possibili: il suo chart chiude alle
  **15:15** e nella regola della slide 55 scrive «chiusura 15.15 giorno precedente», quindi il
  suo `CloseD(1)` è probabilmente quello delle 15:15; e «di tutta la sessione» può voler dire
  la sessione Globex completa. Sono le varianti 1 e 2 sotto.

### 3. Uscita a tempo: fine del cash, 15:00 CT

L'autore non ne dà una: la sua curva finisce alle 15:15 di ogni giorno, cioè il trade resta
aperto fino a stop, target o fine sessione. La prop chiede flat intraday e Lucid chiude alle
15:45 CT: **15:00 CT** è la fine del cash, il momento in cui si forma la chiusura che fa da
riferimento al giorno dopo, e cambia la regola dell'autore di un quarto d'ora al massimo.
Un'uscita alle 10:30 CT (fine della price discovery, slide 39-43) sarebbe più vicina alla tesi
«primi 15-30 minuti», ma è un'invenzione nostra che cambia il WR: è la variante 3, non la base.

### Le percentuali su `$SPX.X`, non su `@ES`

`@ES` di TradeStation è **aggiustato all'indietro per somma** (`Rebalancing.txt`: gennaio
2024 a 5.448 contro ~4.770 reali; più indietro lo scarto cresce). Le distanze in punti sono
giuste, le percentuali no: nel 2020 lo 0,1% calcolato sul prezzo aggiustato sarebbe un 20-30%
più largo in punti di quello vero, e l'IS sarebbe misurato con una soglia diversa dall'OOS.
La regola parla di percentuale del prezzo vero («0.1% (7 punti oggi)»). Quindi: **livelli e
distanze su `@ES`, scala `P` dalla chiusura di ieri dell'indice cash `$SPX.X`**, che sta a
meno dell'1% dal future non aggiustato (il basis): su una soglia di 7 punti l'errore è 0,07
punti. È la stessa soluzione di `Rebalancing` (data3 `$SPX.X`). Se un giorno `$SPX.X` manca,
quel giorno non si trada (e il log lo dice).

## I numeri dell'autore (slide 17-18)

Performance summary TradeStation, `@ES.D` 1 min, 11/10/2006 → 09/10/2026, 1 contratto. Costi
non dichiarati: il summary non li mostra, quindi li tratto come **lordi**.

| | tutti | long | short |
|---|---|---|---|
| trade | **1.868** | 912 | 956 |
| WR | **65,15%** | 65,57% | 64,75% |
| avg trade | **$18,44** | $24,31 | $12,84 |
| vincita media / perdita media | $306,39 / $524,69 (**0,58**) | 0,59 | 0,58 |
| PF | **1,10** | 1,14 | 1,07 |
| trade migliore / peggiore | $787,50 / **−$1.775** | | |
| net | $34.450 | $22.175 | $12.275 |

**Letto dalla curva della slide 17** (a occhio, ±$2.000): ~$19.000 a inizio 2020, ~$40.000 a
fine 2024, picco ~$45.000 nel 2025-26 e ~$35.000 al 09/10/2026. Cioè: **il nostro IS è il tratto
migliore della sua curva** (quasi tutto il guadagno nel salto fra fine 2023 e il 2024; 2020-22
piatto, con il buco del marzo 2020), e **il nostro OOS è in calo già nella sua curva**.

**I costi lo mangiano.** Il suo avg trade lordo è $18,44 su vent'anni, ~$45 sul tratto
2020-24. I nostri costi sono **$35 a giro** per contratto ES-equivalente (sotto). Sui vent'anni
l'avg netto sarebbe negativo; sul nostro IS resta ~$10.

## Contaminazione

1. **Tutto il nostro periodo l'autore l'ha già visto.** Il backtest va dal 2006 al
   09/10/2026 senza un OOS dichiarato: le soglie 0,1% / 0,3% / 0,2% sono, nel migliore dei
   casi, scelte su tutto lo storico che noi usiamo come IS **e** come OOS.
2. **Fuori campione pulito: dal 15/10/2026**, il giorno della lezione (il suo backtest finisce
   il 09/10).
3. **Verdetto OOS asimmetrico**, come per le altre strategie del corso: fallire conta pieno;
   passare vale solo come ingresso in prova dal vivo, con il forward dal 15/10/2026.
4. **k = 1**: si gira solo la regola dell'autore con le letture scritte qui.

## Conti, per contratto e per micro

ES $50/punto, MES $5/punto, tick 0,25. `P` è il livello di `$SPX.X`.

| `P` | lap minimo 0,1% | stop 0,3% | target massimo 0,2% | stop ES / MES | target ES / MES |
|---|---|---|---|---|---|
| ~3.250 (2020) | 3,25 pt | 9,75 pt | 6,50 pt | $487,50 / $48,75 | $325 / $32,50 |
| ~4.250 (media IS) | 4,25 pt | 12,75 pt | 8,50 pt | $637,50 / $63,75 | $425 / $42,50 |
| ~7.000 (2026) | 7,00 pt | 21,00 pt | 14,00 pt | $1.050 / $105 | $700 / $70 |

- **Costi:** $35 a giro per ES-equivalente = $3,50 per MES ($0,50 per lato di commissione
  Lucid sul MES + 1 tick di MES, $1,25, per lato; × 10 sul chart `@ES`).
- **WR di pareggio a target pieno 0,2%:** 60% senza costi; con i costi **63,3%** a `P` 4.250,
  **62,0%** a 7.000. Quando il target è la richiusura di un lap fra 0,1% e 0,2% (~0,15% in
  media), il pareggio sale a **~70%**. Il 65% dell'autore è sopra il pareggio solo di poco.
- **Worst day = worst trade** (un trade al giorno): uno stop. **$105 + $3,50 per MES** a
  7.000, ~$120 al massimo storico. Il peggiore dell'autore è $1.775 per ES = **$177,50 per
  MES** (stop saltato). Molto sotto i $500 per micro della via B e il DLL di Lucid ($1.200)
  anche a più micro: **il rischio di questa strategia non è il trade singolo, è la serie di
  stop.**

## Cosa è congelato e cosa è libero

**Congelato:** le tre percentuali (0,1% / 0,3% / 0,2%), la regola del target (il più vicino),
il filtro dentro il range, le definizioni di `C1`, `H1`, `L1`, `O`, `P`, l'ingresso alla barra
delle 08:32, l'annullamento se la barra delle 08:31 ha toccato `C1`, il flat alle 15:00, un
trade al giorno, long e short insieme.

**Libero:** il numero di contratti (1 per i test, 10 per il controllo ×10), la finestra di date
di trading (input), il logging. Gli orari si possono toccare solo per far combaciare il fuso del
chart, non per cambiare la finestra.

## Varianti pre-registrate

Nessuna si gira se la base fallisce la fase 2. Se la base passa, sono **Stage 4** (solo IS,
split-sample sulle due metà, max 3 input) e ognuna conta nel k.

1. **«Ieri» = sessione dell'autore, 08:30-15:15 CT** per chiusura, massimo e minimo (slide 13,
   55, chart `@ES.D`). Più fedele al suo backtest, meno al riferimento strutturale.
2. **Massimo e minimo di ieri sulla sessione Globex completa** (17:00 → 16:00 CT), chiusura
   sempre alle 15:00: la lettura letterale di «di tutta la sessione» (slide 10). Più aperture
   classificate come lap.
3. **Uscita a tempo alle 10:30 CT** (fine della price discovery, slide 39-43; «soprattutto
   primi 15-30 min», slide 11). Atteso: meno stop pieni, meno target, WR in calo.
4. **Filtro dello stacco «normale»** (slide 19 + definizione della slide 55): si trada solo se
   `|O − C1| ≤ 1 deviazione standard delle close a 15 min delle ultime 350 barre RTH`. Ha senso
   solo se la 2 o la base mostrano perdite concentrate sugli stacchi grandi.

Le letture alternative del target (solo chiusura senza tetto; 0,2% fisso) **non sono
varianti**: la prima è contraddetta dal trade migliore dell'autore, la seconda dalla tesi.

## Criteri

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica** (100 giorni) | ingressi solo alla barra delle 08:32 e nel verso giusto (short sui lap up, long sui lap down); niente trade sui giorni con `O` fuori dalla finestra di armamento o con la barra delle 08:31 che tocca `C1`; `C1`, `H1`, `L1`, `P`, stop e target controllati a mano su 5 trade dal log; flat entro le 15:00; max 1 trade al giorno; scaling ×10 esatto | si corregge il codice |
| **2 — IS 2020-2024** | **via A**: t ≥ 2 · WR ≥ 55% · R:R 0,5-1. Se non passa, **via B**: t > 0,5 (k = 1) e trade peggiore ≤ $500 per micro | cimitero |
| **3 — OOS 2025-2026**, una volta | via A: t ≥ 1,3 e WR dello stesso ordine, poi gate marginale · via B: gate marginale contro il book di riferimento (`pipeline_semplice.md`) | cimitero, definitivo |

**Verdetto OOS asimmetrico** (Contaminazione, punto 3).

## Setup del chart (fase 1)

`@ES` **1 min**, sessione **CME RTH 08:30-15:15 CT** (come il `@ES.D` dell'autore), timezone
Exchange, **data2 `$SPX.X` 1 min** con la sua sessione (08:30-15:00 CT). Bar Magnifier attivo
alla risoluzione più fine disponibile per tutto il periodo (la fissa la checklist, uguale in IS
e OOS). Commissione **$17,50 per contratto per lato**, slippage 0, Point Value $50. Lead-in:
il chart parte almeno un giorno di borsa prima della finestra di trading (per l'IS:
`01/12/2019`, trading dal `01/01/2020`).

## Pre-registrazione
- via: A|B          # profilo dichiarato (WR 65%, R:R 0,58-0,67) dentro la via A; se il t non basta, via B
- k-varianti: 1     # solo la regola dell'autore, con le tre letture scritte sopra
- attesa: t IS fra -0,5 e 1,2, centrale ~0,4; WR 62-66%; R:R realizzato 0,55-0,65; ~450-500 trade. Lordo l'autore fa ~$45 a trade sul 2020-24 (t lordo ~2), i $35 di costi lo portano a ~$10 (t ~0,4). Via A quasi esclusa sul t; via B una moneta. OOS atteso negativo: la curva dell'autore cala già nel 2025-26
- kill: fase 2 via A t < 2 o WR < 55% o R:R fuori 0,5-1, poi via B t <= 0,5 o trade peggiore > $500 per micro -> cimitero; fase 3 via A t OOS < 1,3, via B gate marginale fallito -> cimitero definitivo; verdetto OOS asimmetrico, forward pulito dal 15/10/2026
- costi: $17,50 per contratto per lato nel campo commissione di @ES ($0,50 commissione Lucid MES + 1 tick MES $1,25, per lato, x10), slippage 0; $35 a giro per ES-equivalente, $3,50 per MES
