# NQ First5 — checklist Stage 1 (verifica meccanica)

Obiettivo dello Stage 1: **non** capire se guadagna, ma se fa *esattamente* quello che dice
la spec. Nessuna conclusione sul P&L da questo run.

---

## 1. Chart

| | |
|---|---|
| Strumento | **@NQ** |
| Risoluzione | **5 minuti** — obbligatoria, la barra di riferimento è definita su questa |
| Sessione | **Globex 24h**, *non* la RTH CME custom di VaultBreak |
| Timezone | **Exchange (CT)** |
| Periodo | ultimi ~100 giorni di trading |
| Max bars back | **≥ 300** |
| Bar Magnifier | **non serve** (tutti i fill sono a chiusura barra) — servirà allo Stage 4 con `StopPts` > 0 |
| IOG | **off** |

> ⚠️ È l'errore facile della giornata: abbiamo appena costruito la sessione **RTH CME
> custom** per VaultBreak. Qui va la **Globex 24h**. Con la sessione sbagliata l'ADR viene
> calcolato su una finestra diversa e la barra delle 08:35 può non esistere.
>
> **Accaduto davvero al primo giro**: log con `ADR= 0.00` su tutte le righe e **zero righe
> `F5 EOD`**. Il rollover di sessione stava solo nel ramo `else` della finestra
> `SessionOpen..ExitTime`: su un chart RTH quelle barre non esistono e il ramo non scattava
> mai. Ora il rollover scatta **anche al cambio di data**, quindi l'ADR è indipendente dal
> tipo di chart — ma la Globex resta quella prescritta, perché definisce il range di
> sessione su cui l'ADR è tarato.

## 2. Costi (già quelli onesti, non li cambiamo più)

| | |
|---|---|
| Commission | **`7.5$ per Contract`** ($2,50 + 1 tick da $5,00) |
| Slippage | **`0 ticks`** |

Gli ingressi e le uscite sono ordini *at close*, cioè market: un tick di attraversamento
dello spread è l'ipotesi giusta.

## 3. Input per questo run

| input | valore |
|---|---|
| `EMALength` | 12 |
| `SignalTime` | 835 |
| `ExitTime` | 1500 |
| `SessionOpen` | 830 |
| `AllowLongs` / `AllowShorts` | 1 / 1 |
| `UseFilters` | **0** (base case) |
| `StopPts` | **0** |
| `NumContracts` | 1 |
| `TradeStartEL` / `TradeEndEL` | 0 / 0 |
| **`ShowLog`** | **True** |

`ShowLog` è booleano (True/False), non 0/1. Output nel **PowerLanguage Editor → View →
Output Window**, e ricordati di forzare un ricalcolo dopo aver aperto la finestra.

---

## 4. I controlli — tutti devono passare

| # | Controllo | Come si verifica |
|---|---|---|
| 1 | **Un solo trade al giorno**, mai due | List of Trades: una coppia entry/exit per data |
| 2 | **Ingresso sempre alle 08:35** | tutte le entry timbrate 08:35, nessun altro orario |
| 3 | **Direzione coerente col log** | riga `F5 SIG`: `dir=1` → long, `dir=-1` → short, e corrisponde al trade |
| 4 | **Uscita alle 15:00** | tutte le uscite a 15:00 CT |
| 5 | **Zero posizioni overnight** | nessun trade che attraversa la mezzanotte |
| 6 | **Entrambi i lati presenti** | conta long e short: se gli short sono ~0 c'è un bug, è il punto della strategia |
| 7 | **Niente trade nel weekend** | nessuna entry sabato/domenica |
| 8 | **Mezze giornate** | annotare i giorni in cui l'uscita è anticipata da `SetExitOnClose` |
| 9 | **Numero segnali ≈ numero sessioni** | nel log una riga `F5 SIG` per giorno di borsa; se ne mancano, c'è un buco dati sulla barra delle 08:35 |
| 10 | **ADR sensato e crescente** | righe `F5 EOD`: `sessioni=` sale fino a 100+, `ADR20` e `ADR100` in punti NQ plausibili (centinaia) |

## 5. I due controlli che contano davvero

### 5a. Scaling ×10 — **da fare con lo stop acceso**

È il controllo che ha salvato VaultBreak al Gate 1. `SetStopLoss` è **per posizione**, non
per contratto: senza `CurrentContracts` con 10 contratti lo stop varrebbe un decimo. Ma con
`StopPts 0` lo stop non esiste e **il bug non si vedrebbe**.

Quindi tre run, non due:

| run | `StopPts` | `NumContracts` | atteso |
|---|---|---|---|
| A | 0 | 1 | base |
| B | 0 | 10 | ogni metrica **×10 esatta** rispetto ad A |
| C | **200** | 1 | peggior trade ≈ **−200 pt × $20 = −$4.000** + costi |
| D | **200** | 10 | ogni metrica **×10 esatta** rispetto a C |

Se D non scala esattamente, lo stop non è per contratto e va corretto prima di proseguire.

#### Esito del primo giro (30/09/2026) — A/B **passati**, C/D **bocciati**, bug corretto

| run | Net | Trade | % Prof | scala? |
|---|---|---|---|---|
| A `StopPts 0` × 1 | 75.570 | 100 | 57,0% | — |
| B `StopPts 0` × 10 | 755.700 | 100 | 57,0% | ✅ ×10 esatto, trade per trade identici |
| C `StopPts 200` × 1 | 49.695 | 100 | 50,0% | — |
| D `StopPts 200` × 10 | 112.750 | 100 | **19,0%** | ❌ atteso 496.950 |

La causa, letta nella lista trade di D: **71 uscite su 100 alle 08:40** — la barra
immediatamente successiva all'ingresso — tutte a **−20,00 punti esatti**. Venti punti sono
`200 / 10`. In C le 35 uscite a stop sono tutte a **−200,00** precisi.

`SetStopLoss` è per posizione, e il codice moltiplicava per `CurrentContracts`. Ma lo stop
attivo su una barra è quello calcolato alla **chiusura della barra precedente**, che è la
barra d'ingresso: lì la posizione non è ancora aperta, `CurrentContracts` vale 0,
`MaxList(1, 0)` vale 1 e lo stop è $4.000 su una posizione da 10 contratti. Dalla seconda
barra in poi si allarga ai 200 punti giusti — infatti 7 trade muoiono a −200 e la perdita
massima è $40.150, corretta.

> Con 1 contratto `MaxList(1, 0)` restituisce **il valore giusto per caso**. Il difetto è
> invisibile al run base e compare solo moltiplicando la size: è precisamente il motivo per
> cui il test ×10 esiste, e il motivo per cui va fatto **con lo stop acceso**.

Correzione: `SetStopLoss(StopPts * BigPointValue * NumContracts)`. `NumContracts` è la size
che la strategia apre sempre, non dipende dallo stato di riempimento.
(VaultBreak non ha il difetto: gestisce già il caso flat con `Num_Contracts` nel ramo `else`.)

C e D vanno **rifatti** dopo la ricompilazione. A e B restano validi.

#### Secondo giro (08/10/2026) — C e D **passati**, correzione verificata

Rifatti dopo la ricompilazione, su Globex 24h con `ShowLog` True.

| metrica | C (`StopPts 200` × 1) | D (× 10) | D/C |
|---|---|---|---|
| Net Profit | 44.620 | 446.200 | **10,000000** |
| Gross Profit | 196.675 | 1.966.750 | **10,000000** |
| Gross Loss | −152.055 | −1.520.550 | **10,000000** |
| Max Strategy Drawdown | −30.190 | −301.900 | **10,000000** |
| Max Close To Close DD | −25.135 | −251.350 | **10,000000** |
| Commission Paid | 1.492,50 | 14.925 | **10,000000** |
| Trade · % Prof · PF | 99 · 50,5% · 1,293 | 99 · 50,5% · 1,293 | identici |

Ma il numero che chiude davvero la questione sta nella lista trade: **34 uscite a stop in
entrambi i run, tutte a −200,00 punti esatti**, minimo e massimo coincidenti. Peggior trade
−$4.015 con 1 contratto e −$40.150 con 10. Nel run bugato D aveva 71 uscite a −20 punti.

> Due numeri **non** scalano: `Open Position P/L` (−507,50 contro −8.975) e `Avg Monthly
> Return`. La causa non è il codice: l'ultimo trade era **ancora aperto** all'export e i due
> report sono stati generati a cinque minuti di distanza — il `Trading Period` lo dice
> («4 Mths, 19 Dys, 13 Hrs» contro «…13 Hrs, 5 Mins»). I 99 trade chiusi sono identici.

Attenzione a una cosa per il seguito: **A/B e C/D girano su finestre diverse** (14/05→30/09
contro 22/05→08/10). Ogni coppia è coerente al suo interno, che è quello che il Gate 1
chiede, ma i net delle due coppie non si confrontano fra loro.

#### Check 10 — ADR: verificato

Le righe `F5 EOD` ci sono, una per sessione, da `sessioni= 1` a `sessioni= 99`. ADR20 e
ADR100 in centinaia di punti e plausibili per NQ: parte a 258, sale a 651 a fine giugno,
scende a 310 a ottobre. `ratio` resta 1,000 fino alla sessione 20 — corretto per
costruzione, perché finché `rN ≤ 20` le due finestre mediano gli stessi dati — e poi si
stacca (1,21 al picco di giugno, 0,60 a settembre).

La prima riga `F5 SIG` del 22/05 ha `ADR= 0.00`: è la prima sessione, il rollover non è
ancora avvenuto. Non è un difetto.

> **Conseguenza da tenere a mente per lo Stage 2.** Il run arriva a 99 sessioni e
> `regimeOK` richiede `rN >= VolRegimeLongLen` = 100. Con `UseFilters 1` su questa finestra
> la strategia farebbe **zero trade**. Non è un bug: è il warm‑up, ed è esattamente il
> motivo per cui esiste il gate date.

**Restano solo** i controlli 1‑9 sulla lista trade — già verificati meccanicamente su C e D
(100 ingressi tutti alle 08:35, uno al giorno, nessun doppione, nessun overnight, 20 per
giorno della settimana, 47 long / 53 short, 4 uscite `End of Day Exit` nelle mezze
giornate) — e il **gate date** `TradeStartEL` / `TradeEndEL`.

#### Gate date (08/10/2026) — **passato**

Config del run A (`StopPts 0`, 1 contratto, `UseFilters 0`) con le sole due date cambiate:
`TradeStartEL 1260615`, `TradeEndEL 1260831` — cioè 15/06 → 31/08/2026, due giorni di borsa
interni al periodo caricato. **Gli attesi sono stati scritti prima del run.**

| # | Controllo | Atteso | Ottenuto |
|---|---|---|---|
| 1 | Numero di trade | 56 | **56** ✔ |
| 2 | Primo ingresso | 15/06 08:35 | **15/06 08:35** ✔ |
| 3 | Ultimo ingresso | 31/08 08:35 | **31/08 08:35** ✔ |
| 4 | Ingressi fuori finestra | zero | **zero** ✔ |
| 5 | Uscita dell'ultimo trade | 31/08 15:00, normale | **31/08 15:00**, `F5.LX` ✔ |
| 6 | Righe `F5 SIG` | 56 | **56**, dal 15/06 al 31/08 ✔ |
| 7 | Righe `F5 EOD` fuori finestra | continuano | **continuano**: dal 25/05 al 07/10 ✔ |

Il controllo 7 è quello che conta: l'ADR si aggiorna anche nei giorni in cui il gate
impedisce di entrare. Se si fermasse dentro la finestra, il warm‑up dello Stage 2 sarebbe
inservibile — ed è l'unico motivo per cui questo input esiste.

Uscite: 54 alle 15:00, **2 anticipate** alle 12:00 — 19/06 (Juneteenth) e 03/07 (vigilia del
4 luglio). Entrambe mezze giornate vere, gestite da `SetExitOnClose`.

> **Una differenza rispetto al previsto, da registrare.** Avevo scritto che le righe
> `F5 EOD` sarebbero arrivate a `sessioni= 99` come nel run C/D. Sono **98**, e la prima è
> del **25/05** invece che del 22/05: in questo export la sessione del 22/05 non esiste. Non
> è il gate — il blocco dell'ADR non è gatato e infatti continua a stampare fuori finestra —
> ma il **grafico caricato**, che stavolta comincia dopo le 15:00 del 22/05 e quindi non ha
> barre nella finestra 08:30‑15:00 di quel giorno. Conseguenza: gli ADR100 differiscono di
> poco da quelli del run C/D (sessione 21: 509,77 contro 499,95). Non cambia nessuna
> conclusione, ma conferma che **il range del grafico va fissato e verificato a ogni run**.

Da annotare per la variante `StopPts` (non è un gate): **peggior trade −621,50 punti** =
−$12.445 su 1 mini, cioè **$1.244 per micro** su una finestra di soli due mesi e mezzo.
Il budget che conosciamo è ~$200/micro. Senza stop la strategia non è deployabile, come
dichiarato nella spec.

---

## ✅ Gate 1 — **passato** (08/10/2026)

Tutti i controlli della sezione 4, lo scaling ×10 con lo stop acceso e il gate date.
Report in `reports/`:

| File | Cos'è |
|---|---|
| `F5_S1_A_base_x1.xlsx` · `F5_S1_B_base_x10.xlsx` | base case, ×10 esatto |
| `F5_S1_C_stop200_x1_BUG.xlsx` · `F5_S1_D_stop200_x10_BUG.xlsx` | il run che ha trovato il bug dello stop, tenuti come prova |
| `F5_S1_C_stop200_x1_FIX.xlsx` · `F5_S1_D_stop200_x10_FIX.xlsx` | dopo la correzione, ×10 esatto |
| `F5_S1_gate_date_1260615-1260831.xlsx` | gate date |

**Prossimo passo: Stage 2.** Con `UseFilters 1` servono **più di 100 sessioni caricate**,
perché `regimeOK` richiede `rN ≥ VolRegimeLongLen` = 100. Il gate date serve proprio a
questo: si carica storico abbondante e si fanno partire gli ingressi dopo il warm‑up.

### 5b. Gate date `TradeStartEL` / `TradeEndEL`

Serve allo Stage 2 per separare il warm-up (100 sessioni di `VolRegimeLongLen`) dal periodo
valutato, perché in MultiCharts **il range del grafico è anche il range del backtest**.

1. metti `TradeStartEL` e `TradeEndEL` su una finestra interna al periodo caricato;
2. verifica che **non ci siano ingressi fuori** da quella finestra;
3. verifica che una posizione aperta l'ultimo giorno utile **venga comunque chiusa**
   normalmente alle 15:00 (il gate agisce solo sugli ingressi).

Formato EasyLanguage `YYYMMDD`, `YYY = anno − 1900`:

| data | valore |
|---|---|
| 01/01/2020 | `1200101` |
| 30/06/2022 | `1220630` |
| 01/07/2022 | `1220701` |
| 31/12/2024 | `1241231` |

---

## 6. Cosa annotare comunque (non è un gate)

Sono i numeri che useremo allo Stage 0 della variante `StopPts`, che la spec dichiara
**obbligatoria per l'uso prop**:

- **peggior trade in punti**, long e short separati → è il worst day strutturale, e senza
  stop non ha limite;
- **distribuzione long vs short**: numero, WR e avg trade di ciascun lato;
- quante volte il trade avrebbe superato **100 pt di perdita** (≈ $200/micro, il budget che
  sappiamo già essere il massimo sostenibile).

> Il budget lo conosciamo in anticipo, ed è la lezione di ORB e VaultBreak: il 95°
> percentile Monte Carlo deve stare **sotto $2.000 per micro**. Entrambe sono uscite a
> ~$3.110. Tradotto per First5: puntare a un drawdown storico intorno ai **$10.000–12.000**
> con 1 mini. Se dopo lo Stage 2 il base case è molto sopra, lo stop non è una variante
> opzionale — è la strategia.

**Gate 1**: tutti i controlli della sezione 4 e 5 passati. Report salvati in `reports/`.
