# CHECKLIST Stage 1 — VWAP Pullback

Chart `@NQ` 1 min, Globex 24h, timezone Exchange, **2026‑05‑27 → 2026‑10‑13** (~100 giorni,
78 trade). Codice: `VWAP_Pullback.txt` (la v1 ripulita, **non** la v4 del Bridge: vedi la
pre‑registrazione 1 in `SPEC.md`). Commissione **$7,50 per contratto**, slippage 0.
Tutti gli input ai default: `StopMode 1`, `StopSwingLen 20`, `TargetSwingLen 5`,
`MinRR 0`, `MaxStopPoints 0`, `MaxTradesPerDay 1`, `UseEODFlat 1`, `ShowLog 1`.

Report in `reports/`: `VWAP_S1_x1.xlsx`, `VWAP_S1_x10.xlsx`,
`VWAP_S1_log_stopdist.txt` (il log, ridotto a dir/data/ora/close/stop/target).

---

## ✅ Gate 1 — **passato** (13/10/2026)

| # | Controllo | Risultato | |
|---|---|---|---|
| 1 | Trade dove previsto | ingressi **09:11 → 13:58**, tutti dentro `EntryStartTime 900` / `EntryEndTime 1400` | ✅ |
| 2 | Un trade al giorno | nessun giorno con più di uno, su 78 | ✅ |
| 3 | Flat all'ora prevista | 3 uscite `EOD`, **tutte alle 14:56**; **0/78 overnight** | ✅ |
| 4 | SL/TP = quelli della spec | pivot swing e pivot opposto, come scritto | ✅ |
| 5 | P&L ×10 con 10 contratti | **10,000000 esatto** su ogni metrica in dollari | ✅ |
| 6 | Nessun trade nel weekend | solo lun–ven (13/15/17/16/17) | ✅ |

Il flat cade alle 14:56 e non alle 14:55 perché `Time >= EODFlatTime` scatta sulla barra
timbrata 1455 e l'ordine `next bar at market` riempie sulla successiva. Corretto.

**Nessun difetto `CurrentContracts`**: il codice usa bracket a livello di prezzo
(`next bar at activeStop stop`), non `SetStopLoss`, e il test ×10 lo conferma.

### L'offset di un minuto: previsto e innocuo

Pre‑registrato: a 1 minuto `inORB = Time >= 830 and Time < 900` prende le barre 0830…0859,
cioè copre **08:29 → 08:59**, un minuto indietro rispetto alla spec. Verificato il sospetto
collegato: **zero ingressi nella barra timbrata 0900** (il primo è alle 09:11). L'offset
non produce ingressi nell'ultimo minuto dell'opening range.

---

## ⚠️ La misura del rischio (pre‑registrazione 2): **l'unità di rischio non esiste**

Questa misura era pre‑registrata prima del run proprio per essere fatta qui. Ha trovato
qualcosa di peggiore dell'atteso: non «lo stop è troppo grande», ma **lo stop non ha né
pavimento né tetto**.

Distanza di stop sui 78 trade (1 punto NQ = $20; su MNQ = $2):

| | punti | $ per MNQ |
|---|---|---|
| minimo | **0,25** (un tick) | $0 |
| p5 | 1,43 | $3 |
| p10 | 4,40 | $9 |
| p25 | 48,50 | $97 |
| **mediana** | **109,50** | **$219** |
| p75 | 154,69 | $309 |
| p90 | 249,35 | $499 |
| massimo | **386,75** | **$774** |

**Il rapporto fra il minimo e il massimo è 1.547×.** La mediana, $219 per micro, è già
quasi metà del tetto di Gate 2 ($500), e il p90 lo tocca esattamente.

### Due patologie opposte, e solo una ha una leva pre‑registrata

| | casi | conseguenza | leva |
|---|---|---|---|
| **stop troppo stretto** | 8/78 sotto 5 punti, **4/78 a ≤ 1 punto**, uno a **1 tick** | non è uno stop, è rumore: viene colpito subito | **nessuna.** Non esiste un `MinStopPoints`: servirebbe un input nuovo |
| **stop troppo largo** | 8/78 sopra 250 punti (fino a $774/micro) | sfonda la soglia di Gate 2 sul trade peggiore | `MaxStopPoints`, **pre‑registrato** |

Il target ha lo stesso problema: mediana 74 punti, ma il minimo è **0,50 punti = $10 su NQ**,
sotto i $15 di costo andata‑ritorno. R:R da **0,02** a **557**.

I quattro stop a un tick o meno:

| giorno | stop | R:R | P/L |
|---|---|---|---|
| 2026‑09‑01 | **0,25 pt** | 557,00 | −$10 |
| 2026‑05‑27 | 0,50 pt | 7,00 | −$235 |
| 2026‑08‑25 | 0,75 pt | 94,67 | −$260 |
| 2026‑09‑29 | 1,00 pt | 35,25 | −$205 |

Tutti e quattro in perdita, come dev'essere: un R:R nominale di 557 non serve a niente se
lo stop sta a un tick dal prezzo d'ingresso.

---

## I numeri economici di questi 100 giorni — e perché NON sono un giudizio

**Base, come lanciato: 78 trade, net −$28.435, avg trade −$365, PF 0,63, WR 53,8%,
trade peggiore −$6.285 = $628 per MNQ** (già sopra la soglia di $500).

Il motivo della perdita non è il WR, che è 53,8%: è che lo stop mediano (109 pt) è una volta
e mezza il target mediano (74 pt), quindi il 53,8% non basta.

**Questi numeri non chiudono nulla.** Due ragioni, entrambe già scritte:

1. Il Gate 1 chiede meccanica, non economia. L'economia si giudica allo **Stage 2 sull'IS
   2021‑2024**, e questo è un campione di 100 giorni recenti.
2. È la finestra sbagliata per fidarsi: su Gold Asian Range un campione recente di quattro
   mesi ha dato numeri di rischio che sui cinque anni non si sono riprodotti. **Pre‑registrazione 3
   esiste per questo.**

### Il limite superiore con la sola leva non circolare

`MaxStopPoints` è pre‑registrato come input, ma **il valore va derivato dal gate e non dai
dati**. Gate 2 vuole trade peggiore ÷10 ≤ $500; su MNQ 1 punto = $2; quindi il tetto è
**250 punti**. Nessuna scelta a posteriori.

| configurazione | n | net | avg trade | PF | peggiore/micro |
|---|---|---|---|---|---|
| base | 78 | −$28.435 | −$365 | 0,63 | $628 |
| **`MaxStopPoints 250`** (derivato dal gate) | **70** | **−$14.245** | **−$204** | **0,73** | **$405** |
| pavimento 5 + tetto 250 | 62 | −$14.830 | −$239 | 0,72 | $405 |
| pavimento 10 + tetto 250 | 60 | −$15.750 | −$262 | 0,70 | $405 |

Il tetto a 250 risolve il problema del trade peggiore ($405 < $500) e taglia i quattro
disastri — 28/07 −$6.285, 10/06 −$5.840, 29/06 −$5.655, 23/06 −$5.585, tutti con stop oltre
278 punti. **Ma il risultato resta in perdita.**

### La tentazione, scritta per non cederci

Nei dati esiste un taglio che rende tutto positivo:

| | n | net | avg trade | PF | peggiore/micro |
|---|---|---|---|---|---|
| tetto 100 | 33 | **+$4.815** | **+$146** | **1,46** | $188 |
| tetto 50 | 20 | +$1.250 | +$62 | 1,27 | $98 |

**Non si usa.** `MaxStopPoints 100` non è pre‑registrato come valore: sarebbe scelto
guardando il risultato, cioè esattamente l'errore commesso su Gold Asian Range quando una
pre‑registrazione è stata scavalcata su un campione di quattro mesi. Lo scrivo qui perché
un numero visto non si può dimenticare, e la difesa è registrarlo come off‑limits, non
fingere di non averlo visto.

Se si vorrà testare un tetto diverso da 250, va fatto allo **Stage 4**, dopo lo Stage 3, con
il range di valori dichiarato prima e il **test split‑sample** — che è la regola per
qualunque filtro aggiunto.

---

## Cosa serve prima dello Stage 2

1. **`MaxStopPoints 250`**, derivato dalla soglia di Gate 2. Non negoziabile e non circolare.
2. **Un pavimento allo stop.** Richiede un input nuovo (`MinStopPoints`), quindi una modifica
   al codice, e **non ho un modo non circolare per fissarne il valore**: non esiste una soglia
   di gate da cui derivarlo. Serve una misura dedicata, come l'ADR per Gold — la distribuzione
   del range della barra a 1 minuto su @NQ, per sapere sotto quale distanza uno stop è
   indistinguibile dal rumore. Da misurare **prima** di scegliere il numero.
3. Entrambi sono **filtri**, quindi quando verranno applicati devono passare il
   **test split‑sample**.

---

## Misura del rumore (14/10/2026) — `MinStopPoints` = **60**

`VWAP_Noise_Study.txt` sullo stesso chart dello Stage 1. **594 letture = 100 giorni × 6 ore**
(97 a 13:00 e 14:00: tre chiusure anticipate). Log in `reports/VWAP_noise_log.txt`.

### Un giro buttato, e vale la pena ricordarlo

Il primo giro era su un chart a **15 minuti**, non a 1 minuto, e i numeri erano 2–4 volte
troppo grandi (`atr14` mediano 38 punti, impossibile su una barra da un minuto di @NQ).
Scoperto dal confronto con i dati dello Stage 1: se il rumore a 15 minuti fosse stato 148
punti, uno stop mediano da 109,50 punti sarebbe stato dentro il rumore e i 24 target
raggiunti su 78 non si spiegherebbero. Il run è stato scartato.

### La misura, su @NQ 1 minuto

| | min | p10 | p25 | **mediana** | media | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|
| `atr14` | 4,18 | 7,79 | 10,25 | **16,01** | 19,36 | 24,82 | 36,45 | 96,70 |
| `r5` | 7,25 | 14,25 | 20,75 | **32,50** | 41,98 | 51,25 | 80,00 | 208,75 |
| **`r15`** | 11,50 | 26,83 | 38,00 | **60,00** | 76,80 | 97,50 | 145,90 | 521,25 |
| `r30` | 18,50 | 41,08 | 54,50 | **88,50** | 113,11 | 146,12 | 216,35 | 897,25 |

Controprova interna: le escursioni scalano con la **radice del tempo**, come devono.
`r15/r5` = 1,82 contro √3 = 1,73 · `r30/r15` = 1,42 contro √2 = 1,41. La misura è sana.

### La regola pre-registrata, applicata

> `MinStopPoints` = mediana di `r15`, arrotondata al punto intero.

**Mediana di `r15` = 60,00 → `MinStopPoints = 60` punti = $120 per MNQ.**

La banda ammissibile dello stop è quindi **60 → 250 punti = $120 → $500 per micro**. Il tetto
veniva dal gate, il pavimento dalla misura: **nessuno dei due è stato scelto guardando i
risultati.**

### Il rumore non è costante nella sessione — e questo NON cambia la regola

| ora (CT) | `atr14` | `r15` | `r30` |
|---|---|---|---|
| 09:00 | 30,80 | **108,00** | 183,00 |
| 10:00 | 21,63 | 85,38 | 117,75 |
| 11:00 | 14,58 | 58,75 | 87,62 |
| 12:00 | 12,30 | 48,00 | 70,88 |
| 13:00 | 10,63 | 40,50 | 57,00 |
| 14:00 | 10,34 | **40,00** | 55,50 |

Il rumore alle 09:00 è **2,7 volte** quello delle 14:00. Un pavimento fisso a 60 è quindi
permissivo in apertura e severo in chiusura.

**La regola resta 60.** Era scritta come «la mediana di `r15`», un numero singolo, e si
applica come scritta: cambiarla in un pavimento variabile *dopo* aver visto la dipendenza
oraria sarebbe esattamente l'errore commesso su Gold Asian Range. La dipendenza oraria
diventa una **variante Stage 4 pre-registrata adesso**: pavimento proporzionale all'ATR(14)
del momento invece che fisso — da testare dopo lo Stage 3, con il test split-sample.

---

## Effetto della banda 60–250 sul campione dello Stage 1

Non è un giudizio di gate: sono 100 giorni recenti, e il regime recente ha già ingannato
una volta. Serve a decidere se spendere lo Stage 2.

| configurazione | n | net | avg trade | WR | PF | R:R | peggiore/micro | t |
|---|---|---|---|---|---|---|---|---|
| base | 78 | −$28.435 | −$365 | 53,8% | 0,63 | 0,54 | $628 | −1,54 |
| solo tetto 250 | 70 | −$14.245 | −$204 | 54,3% | 0,73 | 0,62 | $405 | −1,04 |
| **pavimento 60 + tetto 250** | **48** | **−$15.075** | **−$314** | **58,3%** | **0,69** | **0,49** | **$405** | **−1,14** |

### Cosa le due regole risolvono, e cosa no

**Risolvono il rischio**, che era il problema dichiarato:

- banda effettiva degli stop tenuti: **63,75 → 236,75 punti = $128 → $474 per MNQ**, tutta
  dentro il tetto di $500
- WR sale a **58,3%**, sopra la soglia del 55%
- 48 trade su 78 tenuti (62%) → proiezione su cinque anni **~603 trade**, molto sopra la
  soglia di 200

**Non risolvono il P&L**, e la diagnosi è precisa: **R:R mediano 0,49**. Con un R:R di 0,49
il WR di pareggio è 1 / (1 + 0,49) = **67,1%**. Il WR osservato è 58,3%: manca quasi un
9% assoluto. Il target è troppo vicino rispetto allo stop.

### Il pavimento costa soldi, ed è la prova che non è stato scelto per piacere

I 22 trade sotto i 60 punti di stop portavano **+$830 netti** (10 vincenti, 12 perdenti):
togliendoli il netto peggiora. Se avessi scelto il pavimento guardando i risultati non avrei
mai scelto 60. È giustificato dal realismo del rischio, non dal rendimento — che è
esattamente il ruolo che gli era stato assegnato.

Il tetto invece fa il lavoro sul P&L: gli 8 trade sopra 250 punti pesavano **−$14.190**.

### Nessun pavimento salva la strategia

| pavimento (tetto fisso 250) | n | net | avg trade |
|---|---|---|---|
| 20 | 58 | −$16.835 | −$290 |
| 40 | 53 | −$16.885 | −$319 |
| **60** | **48** | **−$15.075** | **−$314** |
| 80 | 43 | −$14.980 | −$348 |
| 100 | 37 | −$19.060 | −$515 |
| 120 | 25 | −$13.865 | −$555 |

Tutti perdono. La conclusione non dipende dal 60: **non esiste un pavimento che rimetta in
piedi questo campione.** È un'informazione utile, perché toglie la tentazione di cercarlo.

### La leva giusta esiste e è già pre-registrata — ma non si tocca adesso

Il problema è il **target**, non lo stop: R:R 0,49 contro un WR di 58,3%. Le varianti Stage 4
già scritte in `SPEC.md` includono **`MinRR 1`** e **«TP fisso in R al posto del pivot»**, che
sono esattamente la leva.

Ma **Stage 3 viene prima di Stage 4**, e Stage 2 prima di Stage 3. Non si anticipa, per la
regola presa dopo i due errori su ORB e VaultBreak.
