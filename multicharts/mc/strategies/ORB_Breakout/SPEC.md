# SPEC — ORB_Breakout (Stage 0)

**Ipotesi**: se NQ chiude sopra il range dei primi 30 minuti di cash session, il
movimento continua nella giornata abbastanza spesso da pagare uno stop al lato opposto
del range con target 1R.
**Perché**: flussi che possono operare solo dopo le 09:30 NY (fondi, algos benchmarked
alla sessione) + momentum intraday documentato (Market Intraday Momentum, JFE 2018;
Zarattini 2023). Chi perde: chi fade l'apertura. Edge validato dal corso su NQ 2021‑26
(823 trade, WR 58%, avg $183, PF 1.28).

| | |
|---|---|
| Famiglia | trend / breakout |
| Strumento · TF · sessione | @NQ · 5 min · Globex, chart in ora Chicago |
| Range | 08:30–09:00 CT |
| Entry | prima barra che chiude > range high (long only) |
| Stop | range low |
| Target | 1R |
| Time exit | 14:00 CT |
| Trade/giorno | 1 |
| Profilo prop | WR ~58%, R:R 1 → ok |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi (una volta sola).
**Varianti pre‑registrate (Stage 4)**: TP 0.5R; cutoff ingressi 11:00 CT; filtro delta
(UpTicks−DownTicks ≥ 200); `MaxRisk_USD` (vedi griglia sotto); short leg (atteso: no);
**ingresso su ritracciamento a VWAP ancorato al breakout** (1–1.5 SD, stop 2×ATR — dalla
live Quant VWAP, vedi `mc/strategies/Quant_VWAP/NOTES.md`; NON adottare il suo TP 3×,
incompatibile col profilo prop).
**Kill**: fallisce un gate della pipeline → cimitero. Non si ottimizza il range (30 min
è il modello validato; 60 min = variante IB, strategia separata). Nota di robustezza: in
una live indipendente l'ottimizzazione della durata del range su NQ ha il picco a 30–32
min e tiene out‑of‑sample → i 30 min stanno in un cluster, non su un picco fittato.

Stato: Stage 1 ✔ (report ES/NQ in `reports/`).

## Stage 4 — `MaxRisk_USD`: griglia e criterio, scritti prima del run (29/09/2026)

Il valore «250 pt» pre‑registrato allo Stage 0 era una stima al buio: sullo storico vero
salta **3 trade su 395**, quindi non cambierebbe niente. L'input resta quello
pre‑registrato; qui si fissa la griglia, come previsto dallo Stage 4.

**Distribuzione del range di apertura** (= distanza dello stop) sull'IS 2020‑2024,
ricostruita dalle uscite in SL e TP del run base:

| | punti | rischio 1 NQ | 1 micro | % trade saltati |
|---|---|---|---|---|
| mediana | 90 | $1.805 | $180 | — |
| p80 | 125 | $2.495 | $250 | 20% |
| p90 | 154 | $3.080 | $308 | 11% |
| p95 | 188 | $3.765 | $376 | 4% |
| p99 | 240 | $4.790 | $479 | 1% |
| max | 334 | $6.680 | $668 | — |

**Griglia**: `0` (base case) · `2500` · `3000` · `4000` · `5000`. Passi larghi, cinque
punti. Sotto $2.500 si salterebbe oltre un terzo dei trade: non è più togliere la coda,
è un'altra strategia.

**Come si gira** (deciso 29/09, prima dei risultati): tre **ottimizzazioni**, una per
periodo (IS intero, 1ª metà, 2ª metà), con `MaxRisk_USD` da **2500 a 5000 step 500**. Il
base case `0` è già misurato. I valori intermedi (3500, 4500) servono a **giudicare la
forma della curva** per il criterio del cluster, **non** a scegliere il migliore: la
decisione resta ancorata ai valori dichiarati sopra. Se un intermedio fosse il massimo
assoluto ma i dichiarati adiacenti fossero mediocri, la variante si scarta.

**Criterio di scelta, fissato ora**:
1. deve migliorare l'avg trade in **entrambe** le metà dell'IS (2020‑01→2022‑06 e
   2022‑07→2024‑12), non solo nel totale;
2. `n` deve restare ≥ 200;
3. si sceglie un valore **in un cluster**: se due soglie adiacenti funzionano e quella in
   mezzo no, il risultato è rumore e la variante si scarta;
4. non si scende sotto $2.500 nemmeno se i numeri migliorassero.

**Cosa può e non può fare** — scritto prima per non raccontarsela dopo:
- **può** sistemare il criterio sul peggior trade, per costruzione: con soglia $4.000 la
  perdita massima diventa $4.000, cioè $400 per micro, sotto il limite di $500;
- **probabilmente non può** sistemare il drawdown. Servirebbe passare da $36.290 a
  < $12.500, un terzo. Ma quel DD non è un trade mostruoso: è una **serie di perdite
  normali** a marzo 2020, e tagliare la coda non toglie una serie perdente;
- **gioca contro**: con `TP_RR 1.0` il target è largo quanto il range, quindi saltare i
  giorni a range largo elimina anche le **vincite più grosse**. L'effetto sul PF è
  genuinamente incerto e potrebbe essere negativo.

**Contesto del gate**: `DD ÷ 10 = $3.629` contro il max drawdown Apex di **$2.500**. Così
com'è, anche a 1 solo micro la strategia avrebbe fatto saltare un conto funded nel marzo
2020. La soglia del gate non è arbitraria: è la regola del conto.

## Configurazione adottata allo Stage 4 (30/09/2026)

```
MaxRisk_USD = 3000      (salta i giorni con range > 150 pt)
UseDeltaFilter = 1      (DeltaThreshold 200, valore del corso, NON ottimizzato)
TP_RR = 1.0             (invariato)
```

Due input su tre concessi. Percorso, con lo split‑sample come unico arbitro:

| variante | 1ª metà | 2ª metà | esito |
|---|---|---|---|
| `MaxRisk 2500` | −0,39 → 113,43 ✓ | 162,67 → 148,52 ✗ | **bocciata** |
| `MaxRisk 3000` | −0,39 → 107,96 ✓ | 162,67 → 183,88 ✓ | **adottata** |
| `TP_RR 0.5` | 107,96 → 59,82 ✗ | 183,88 → 130,56 ✗ | **bocciata** |
| `UseDeltaFilter 1` | 107,96 → 130,79 ✓ | 183,88 → 188,51 ✓ | **adottata** |

**Risultato IS 2020‑2024**: 674 trade · WR 57,6% · avg $161,36 · PF 1,304 · R:R 0,96 ·
DD $15.697 · peggior trade $2.995 · nessun anno oltre il 37% del net.

**Gate 2: 7 criteri su 8.** Resta `DD ÷ 10 = $1.570` contro la soglia **$1.000**
(metà dell'MLL di LucidFlex 50k). Servirebbe scendere a $10.000 sul mini, −36%.

**Riserva sul filtro delta**: nella seconda metà il guadagno è +2,5% su 357 trade, cioè
dentro il rumore; il valore sta quasi tutto nella prima metà (+21%). Possibile che il
segnale di order flow fosse più forte nel regime 2020‑2022. Da tenere presente come
aspettativa bassa allo Stage 5.

**Nota**: il max drawdown dell'IS ora cade nella **seconda metà** (ott. 2024), non più a
marzo 2020. La strategia non ha più un evento eccezionale che domina il profilo di rischio.

**Ultima variante disponibile** (terzo e ultimo input dello Stage 4): cutoff ingressi alle
11:00 CT. Aspettativa dichiarata prima del test: **debole**. Toglie i breakout tardivi, che
sono mediamente peggiori, ma non c'è una ragione strutturale per cui debba comprimere di un
terzo una serie perdente. Se non basta, l'ORB non supera il Gate 2, e la conclusione da
trarre è che con lo stop pari all'intero range di apertura la strategia è troppo grande per
un conto con $2.000 di margine — non che il protocollo abbia sbagliato.

## Stage 4 chiuso — Gate 2 NON superato (30/09/2026)

Terza e ultima variante, `UseEntryCutoff 1` alle 11:00 CT: **passa lo split‑sample**
(1ª metà 130,79 → 143,14; 2ª metà 188,51 → 227,38) ma **non risolve il drawdown**
(15.697 → 15.017, −4,3%). Aspettativa dichiarata prima del test: "debole". Confermata.

**Configurazione finale**: `MaxRisk_USD 3000` · `UseDeltaFilter 1` (soglia 200) ·
`UseEntryCutoff 1` alle 11:00 · `TP_RR 1.0`. **Tre input su tre**: lo Stage 4 è chiuso.

| Criterio | Soglia | Finale | |
|---|---|---|---|
| n | ≥ 200 | 550 | ✓ |
| avg trade | ≥ $70 | $188,63 | ✓ |
| PF | ≥ 1.2 | 1,337 | ✓ |
| WR | ≥ 55% | 58,9% | ✓ |
| R:R | 0.5–1 | 0,93 | ✓ |
| peggior trade ÷ 10 | ≤ $500 | $300 | ✓ |
| nessun anno > 50% | — | 31,5% | ✓ |
| **DD ÷ 10** | **≤ $1.000** | **$1.502** | **✗** |

Percorso del drawdown: $36.290 → $18.991 (MaxRisk) → $15.697 (delta) → $15.017 (cutoff).
Dimezzato e mezzo, ma il bersaglio era $10.000.

**Perché non si va oltre**: i tre input concessi sono esauriti. Continuare a cercare
varianti dopo aver visto il fallimento è precisamente ciò che il protocollo vieta.

### Limite del criterio, da tenere presente altrove

Lo split‑sample misura l'**avg trade**, e qualunque filtro che tolga trade marginali lo
alza anche riducendo il profitto totale: 674 → 550 trade, net $108.759 → $103.746. Il
cutoff ha «vinto» pagando $5.013. Su LucidFlex questo pesa meno del previsto, perché **non
c'è limite di tempo** per superare la valutazione — ma il criterio va guardato insieme al
net, non da solo.

### Diagnosi

Il drawdown non è un difetto correggibile con filtri: è l'**unità di rischio**. Lo stop è
l'intero range di apertura, una quantità che decide il mercato. Mediana $180 per micro,
tetto $300 dopo `MaxRisk`. Con $2.000 di MLL, cinque perdite consecutive — che nei cinque
anni sono accadute — valgono il 75% del conto.

## Override registrato del Gate 2 — 01/10/2026

**Decisione**: il Gate 2 è dichiarato superato **per override esplicito**, non per merito.
Unico criterio non rispettato: `DD ÷ 10 = $1.502` contro la soglia di $1.000.

**Motivazione**: la soglia del Gate 2 è fissata al **50% dell'MLL** perché misura un
**singolo percorso storico**, e il margine serve a coprire la coda ignota. Lo Stage 3
misura la stessa cosa con uno strumento migliore — il 95° percentile di 1000 reshuffle,
che *è* la coda — e per questo la sua soglia è il 100% dell'MLL. Andare allo Stage 3 non
salta un controllo: sostituisce uno stimatore debole con uno forte, su un criterio già
scritto prima del test.

**Condizioni della riserva** (senza queste è una nota che nessuno rilegge):
1. **Scadenza**: se al Gate 3 il DD al 95° percentile ÷ 10 supera **$2.000**, è un no
   definitivo. Non si ridiscute, non si cercano altre varianti — lo Stage 4 è chiuso.
2. **Si porta avanti**: la riserva resta segnata fino allo **Stage 7**, dove il simulatore
   prop dà la risposta vera sulla domanda che conta davvero, cioè la probabilità di
   toccare $48.000 prima di arrivare a $52.100.
3. **Resta a verbale**: se un domani l'ORB deludesse in esercizio, questo è il punto in cui
   abbiamo scelto di forzare, con la data.

**Attesa dichiarata prima del Monte Carlo**: il 95° percentile del DD sta tipicamente fra
1,3 e 1,8 volte il massimo storico. Da $15.017 significa **$1.950–$2.700 per micro**, cioè
a cavallo della soglia. È genuinamente incerto — ed è esattamente il motivo per cui vale la
pena misurarlo invece di discuterne.

**Quello che l'override non cancella**: la diagnosi resta quella scritta sopra. Lo stop
pari all'intero range di apertura è un'unità di rischio che decide il mercato, non noi. Una
spec separata con **stop a rischio fisso** resta la correzione strutturale, e va fatta come
strategia nuova — non come salvataggio di questa.

## Stage 3 — Gate 3 NON superato. Fine del percorso (01/10/2026)

Monte Carlo built‑in, 1000 reshuffle, 100% dei trade, sulla configurazione finale
(550 trade, PF 1,35, avg $193,97, peggior perdita $2.990 — verificata).

| | close‑to‑close |
|---|---|
| DD storico (base equity curve) | $12.125 |
| Simulazione migliore | $9.830 |
| **DD 95° percentile** | **$31.210** → **$3.121 per micro** |
| Simulazione peggiore | $42.855 |
| **Soglia Gate 3** | **$2.000** |

**Supera del 56%.** Per la condizione 1 della riserva registrata il 01/10, è un **no
definitivo**: non si ridiscute e lo Stage 4 resta chiuso.

**Errore di stima da annotare**: avevo previsto un 95° percentile fra 1,3 e 1,8 volte il
massimo storico. Il rapporto reale è **2,57×**. Con WR 59% e R:R 0,93 il risultato dipende
quasi solo dall'**ordine** di vincite e perdite: nello storico la serie perdente più lunga
è 5, ma su mille rimescolamenti emergono serie molto più lunghe, e ogni perdita vale fino a
$3.000. È esattamente ciò che un singolo percorso storico non può mostrare.

### Esito

L'ORB **così come è specificata** non è utilizzabile su un conto con $2.000 di MLL. Non
perché non abbia un edge — ne ha uno stabile, PF 1,34 e WR 59% su cinque anni, positivo in
entrambe le metà dell'IS — ma perché **l'unità di rischio è troppo grande per il conto**.

**L'OOS 2025+ non è stato toccato.** Resta intatto per la eventuale spec con stop a rischio
fisso, che è la correzione strutturale e va aperta come **strategia nuova** allo Stage 0.

### Calibrazione utile per le altre cinque strategie

Un solo dato, quindi da confermare, ma indicativo: se il rapporto **2,57×** fra 95°
percentile Monte Carlo e massimo storico fosse tipico, per superare il Gate 3 servirebbe un
DD storico ÷ 10 sotto i **~$780**. La soglia del Gate 2 ($1.000, cioè il 50% dell'MLL) è
quindi un filtro **leggermente permissivo** rispetto a ciò che il Gate 3 chiede davvero.
Non la cambiamo su un dato solo, ma è bene saperlo prima di investire tempo su una
strategia che al Gate 2 passa per un soffio.
