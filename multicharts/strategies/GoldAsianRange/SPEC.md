# SPEC — Gold Asian Range Breakout (Stage 0)

**Ipotesi**: durante la sessione asiatica l'oro forma un range compresso; all'arrivo
della liquidità di Londra/USA la rottura di quel range tende a proseguire fino a metà
mattina USA.
**Perché**: gli ordini vengono piazzati **nell'istante** in cui il range chiude, senza
gap fra livello e ordine (è ciò che uccide i breakout "del giorno prima"); il flusso
europeo/USA è più grande di quello asiatico e ne rompe l'equilibrio. Chi perde: chi
vende il range ai suoi estremi. Vincitore Strategy of the Month lug/ago 2026 (live: PF
1.64 poi 3.28); ricerca: Sharpe 0.89, PF 1.18, WR ~34%.
Ruolo nel basket: **altro asset** (agosto 2026 NQ piatto, oro no) e altro orario.

| | |
|---|---|
| Famiglia | trend / range breakout |
| Strumento · TF · sessione | @GC (sviluppo) → MGC · 15 min · Globex, chart CT |
| Range | 21:00–01:00 NY = **20:00–00:00 CT** (attraversa la mezzanotte: il codice del corso gestisce il wrap) |
| Entry | buy stop al range high, sell stop al range low, OCO, alla chiusura del range |
| Stop | 1.0 × ampiezza del range |
| Target | nessuno (variante A) |
| Time exit | 11:00 NY = **10:00 CT** |
| Trade/giorno | 1 |
| Profilo prop | **variante A non lo rispetta** (WR 34%, R:R > 1): candidata solo come diversificatore funded a size piccola. **Variante B** (pre‑registrata): TP = 1R (poi 0.5R) per il profilo eval. |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: B = TP 1R / 0.5R; StopFrac 0.5/0.75; long only;
finestra range 22:00–01:00 CT.
**Note**: GC = $100/pt (tick 0.10 = $10), MGC = $10/pt. Range tipico $10–25 → rischio
$1.000–2.500 per GC, $100–250 per MGC. Nel report del corso il chart era in ora NY con
day boundary 17:00: verificare che con il chart CT le finestre coincidano.
**Kill**: gate pipeline. La variante A entra in pipeline solo per lo Stage 8 (basket),
non per l'eval.

---

# Stage 1 — **Gate 1 passato** (09/10/2026)

Dettaglio e prove in `CHECKLIST_Stage1.md`, report in `reports/`. Qui solo ciò che
**modifica la spec**. Il corpo sopra resta com'era scritto prima dei run: è la
pre-registrazione e non si riscrive.

### Risolto: la finestra del range con chart CT

La domanda aperta («nel report del corso il chart era in ora NY con day boundary 17:00:
verificare che con il chart CT le finestre coincidano») è chiusa: la finestra è stabile e
identica su tutte le giornate.

> ⚠️ **Corretto il 13/10/2026.** Qui era scritto «`barre= 16` e `armTime= 0` = 20:00 → 00:00
> esatte, MC timbra la barra di mezzanotte `0` e non `2400`». **Falso per il template 24/7**,
> che è quello che usiamo: valeva solo per il template COMEX del primo giro invalidato. Con
> il 24/7 MC timbra la mezzanotte **`2400`**, `Time >= 2000` la include, e il log dà
> **`barre= 17`, `armTime= 15`**. La finestra misurata è **19:45 → 00:00 (4h15)**, cioè 15
> minuti più larga della spec. Costante su tutte le giornate, quindi la misura è consistente
> e tutte le statistiche fatte finora restano valide fra loro. Vedi
> `CHECKLIST_Stage1.md`, sezione gate date.

### Corretto: sessione del chart

Il template `COMEX: Metals Futures (Electronic)` **non va usato**: lascia il chart senza
barre fra 07:45 e 14:15 e manda il time exit sulle 14:15. Serve un template **24/7**.

### Corretto: ampiezza del range, quindi rischio per trade

| | spec (assunto) | misurato |
|---|---|---|
| range | $10–25 | **mediana 37,8 pt**, media ≈ 42 pt |
| rischio per GC | $1.000–2.500 | **$3.780** mediano |
| rischio per MGC | $100–250 | **$378** mediano, **$442** nel caso peggiore del campione |

Da 1,5 a 3,8 volte l'assunzione. **Resta sotto la soglia di Gate 2** sul trade peggiore
(÷10 ≤ $500): $442. È la prima strategia della pipeline la cui unità di rischio entra nel
budget dell'MLL — le tre su @NQ morivano esattamente qui.

### Corretto: il profilo della variante A

| | spec (dalla ricerca del corso) | misurato (78 trade, 4 mesi) |
|---|---|---|
| WR variante A | ~34% | **57,7%** |
| avg win / avg loss | > 1 | 1,50 |
| PF | 1,18 (ricerca) / 1,64–3,28 (live) | 2,04 |

Il WR 34% non si riproduce. Ipotesi: il time exit a 10:00 CT chiude in piccolo utile
molte posizioni che altrimenti si girerebbero in perdita. Da verificare sui 5 anni dello
Stage 2.

**Conseguenza sulla pre-registrazione**: allo Stage 2 vanno **entrambe** le varianti, non
solo la B. La regola «Gate 2 si giudica sulla variante B» era motivata dall'attesa WR 34%
della A; quell'attesa è smentita da un dato di meccanica, non da una scelta a posteriori
sui risultati. Le varianti Stage 4 (`StopFrac` 0.5/0.75, long only, finestra 22:00–01:00)
restano come scritte.

### Aperto

- **ADR dell'oro nel periodo non misurata**: 37,8 punti di range asiatico su un
  sottostante a $4.100–4.400 vanno rapportati al range giornaliero medio. Se il range
  asiatico è una frazione dominante dell'ADR, lo stop «tutto il range» è strutturalmente
  sovradimensionato e la variante `StopFrac` < 1 diventa il caso base, non un'alternativa.
- **Gate date** non ancora eseguito.

---

# ADR misurata (13/10/2026) — la condizione pre-registrata non è soddisfatta

Prove in `CHECKLIST_Stage1.md`. n = 84 giornate.

La regola era scritta prima di misurare: «se il range asiatico è una frazione dominante
dell'ADR, lo stop *tutto il range* è strutturalmente sovradimensionato e `StopFrac` < 1
diventa il caso base».

**`asia / h24` = 0,447 mediano.** Il range asiatico è meno della metà dell'escursione
giornaliera: la condizione **non** è soddisfatta.

→ **`StopFrac 1.0` resta il caso base dello Stage 2.** Le varianti 0.5/0.75 restano allo
Stage 4 dove erano pre-registrate.

Due dati che si portano dietro:

- **Il target a 1R è raggiungibile**: `trade / asia` = 1,531 mediano. 1R è impossibile
  anche in teoria solo nel **21,4%** dei giorni — che combacia col 28% di target
  realizzati dalla variante B. A `TP_RR 0.5` la quota scende all'**1,2%**.
- **Il 90° percentile del rischio sfora**: con `StopFrac 1.0` il rischio per MGC è $390
  mediano ma **$662 al p90** e $852 nel caso peggiore, contro una soglia di Gate 2 di
  $500 sul trade peggiore. Il trade peggiore realizzato era $442 perché **i giorni col
  range più largo tendono a non generare trade** (38% senza trade nel decile più largo
  contro 4,9% complessivo: un range largo è più difficile da rompere in 10 ore). È un
  meccanismo, non fortuna — ma è una proprietà del campione, non una garanzia.
  **Da sorvegliare al Gate 2.**

---

# Stage 2 — IS 2020‑2024: **Gate 2 fallito da entrambe le varianti**

Chart 2020‑01‑03 → 2024‑12‑31, 1 contratto, $12,50/contratto, slippage 0, Bar Magnifier
1 min, template 24/7. Report in `reports/GAR_S2_IS_A_tp0.xlsx` e `GAR_S2_IS_B_tp1.xlsx`.
**1.280 trade** per variante, ~256 all'anno, nessun anno con dati mancanti.

| criterio | soglia | A (`TP_RR 0`) | B (`TP_RR 1`) |
|---|---|---|---|
| n | ≥ 200 | **1.280** ✅ | **1.280** ✅ |
| avg trade | ≥ $140 (GC) | **$60** ❌ | **$21** ❌ |
| Profit Factor | ≥ 1.2 | **1,152** ❌ | **1,062** ❌ |
| WR | ≥ 55% | **42,6%** ❌ | **52,7%** ❌ |
| avg win / avg loss | 0,5–1 | **1,554** ❌ | **0,955** ✅ |
| DD ÷ 10 | ≤ $1.000 | **$2.186** ❌ | **$2.358** ❌ |
| trade peggiore ÷ 10 | ≤ $500 | **$498** ✅ | **$498** ✅ |
| nessun anno > 50% | | 41% (2021) ✅ | **66% (2024)** ❌ |

Tre criteri su otto passati da ciascuna.

## La dimostrazione: nessuna variante pre‑registrata può passare

Non serve spendere run. L'avg trade richiesto è $140 **netti**; il costo andata‑ritorno su GC
è $25; quindi serve un edge **lordo** di **$165 per trade**.

| | edge lordo misurato | serve | fattore mancante |
|---|---|---|---|
| A | **$85** | $165 | **1,9×** |
| B | **$46** | $165 | **3,6×** |

Cioè: **anche azzerando del tutto i costi**, nessuna delle due arriva alla soglia. Una
variante può spostare dove cade l'edge fra WR e R:R, non può moltiplicarlo per due o per
quattro.

Verificato anche l'unico asse che poteva cambiare il quadro, `long only` (pre‑registrato):
va nella **direzione opposta**. Su oro 2020‑2024 il lato buono è lo short.

| | n | avg trade | WR | PF |
|---|---|---|---|---|
| A long | 654 | $42 | 45,3% | 1,111 |
| A short | 626 | **$79** | 39,8% | 1,191 |
| B long | 654 | $23 | 53,4% | 1,069 |
| B short | 626 | $20 | 51,9% | 1,055 |

`short only` su A darebbe $79 contro $140, con WR 39,8% e R:R 1,80: fallisce comunque tre
criteri. E `long only` su B peggiora la concentrazione annuale (2024 al 76%).

## L'edge non è distinguibile da zero

| | avg trade | sd | SE | t | IC 95% |
|---|---|---|---|---|---|
| A | $60,0 | $1.132 | $31,6 | **1,89** | **−$2 … +$122** |
| B | $21,4 | $835 | $23,3 | **0,92** | **−$24 … +$67** |

**Entrambi gli intervalli di confidenza contengono lo zero**, su 1.280 trade e cinque anni.
Per portare la variante B a un t = 2 servirebbero **6.085 trade** a questo livello di edge,
cioè ventiquattro anni di dati.

## ✉️ Causa di morte: **A — edge assente**

È la **prima morte per causa A** della pipeline. ORB, VaultBreak e NQ First5 erano tutte **B**
(edge presente, unità di rischio fuori dall'MLL).

Qui è l'opposto, e vale la pena notarlo: **l'unità di rischio passa** — trade peggiore $498
per MGC contro una soglia di $500. Il muro che ha ucciso le tre strategie su @NQ non c'è.
Quello che non c'è è l'edge.

La variante A conserva un edge direzionale marginale (t = 1,89) ma **non può raggiungere
WR ≥ 55% per costruzione**, come la spec diceva allo Stage 0. Con l'IC che contiene lo zero
è troppo debole per occupare uno slot del basket allo Stage 8. **Chiusa anche lei.**

## Correzione a quello che avevo scritto dopo lo Stage 1

Dopo il Gate 1 avevo scritto che il WR 34% della ricerca «**non si riproduce**» (misurato
57,7%) e ne avevo concluso che allo Stage 2 andassero **entrambe** le varianti, non solo la B
come pre‑registrato.

Su 1.280 trade e cinque anni il WR della variante A è **42,6%**: molto più vicino al 34%
della ricerca che al 57,7% del 2026.

**La pre‑registrazione originale era giusta e la mia revisione era sbagliata.** Avevo
scavalcato un giudizio pre‑registrato sulla base di **78 trade e quattro mesi**. È
esattamente l'errore che il protocollo esiste per impedire, e l'ho fatto io, non il
protocollo.

## Perché lo Stage 1 sembrava promettente: due regimi diversi

| | 2026 (4 mesi, Stage 1) | 2020‑2024 (5 anni, Stage 2) |
|---|---|---|
| range mediano | **39,05 pt** | distanza di stop mediana **6,60 pt** (p90 11,22) |
| range più largo | **85,20 pt** in 4 mesi | **49,50 pt** in 5 anni |
| escursione giornaliera mediana | 92,90 pt ≈ 2,2% | — |

**Il range più largo di quattro mesi del 2026 supera il più largo di cinque anni
precedenti.** Il 2026 è il regime anomalo, non il 2020‑2024.

Il meccanismo che lega le due cose: lo stop **è** l'ampiezza del range, quindi l'edge per
trade scala con la volatilità realizzata — **ma i costi no**. Con un range di 39 punti i $25
di costo sono rumore; con un range di 7 punti si mangiano metà dell'edge lordo.

Nota sul metodo, e non è una correzione al gate: il Gate 1 chiede «meccanica corretta al
100%» e non ha mai preteso di validare l'unità di rischio. I $442 di trade peggiore per MGC
dello Stage 1 li ho letti **io** come una buona notizia, extrapolando da quattro mesi.
L'errore è nella mia inferenza, non nel gate.

## Nota sui dati: @GC è back‑adjusted

Il prezzo medio d'ingresso nel 2020 è **2.459**, mentre l'oro nel 2020 stava fra $1.500 e
$2.070. Il continuous @GC è quindi **back‑adjusted**: i livelli storici sono traslati di
~$900 all'inizio del 2020.

Non invalida questo Stage 2: l'aggiustamento additivo **preserva le differenze di prezzo**,
quindi ampiezze di range, distanze di stop e P&L in dollari sono corretti. Ma **qualunque
logica in percentuale di prezzo su @GC è inaffidabile**, e questo è esattamente il blocco
mai rimosso di **DriftPullback**, il cui drift è `(Close − Close[n]) / Close[n]`.
