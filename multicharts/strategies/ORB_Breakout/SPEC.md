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

---

# Riapertura e pre-registrazione OOS (15/10/2026)

**Perche si riapre.** Era chiusa al **Gate 3**, che e stato **ritirato dalla pipeline**: la sua
logica (DD al 95esimo percentile ÷10 contro l'MLL) e lo stesso errore del RATIO, cioe trattare
la eval come «sopravvivere a cinque anni» invece che come primo passaggio su finestra corta e
ripetibile. Col metro prop attuale la variante **cutoff11** supera il Gate 2:

`MaxRisk_USD 3000` · `UseDeltaFilter 1` (soglia 200) · `UseEntryCutoff 1` alle **11:00** ·
`TP_RR 1.0` · `AllowShort 0` · 550 trade · **t 2,95** · WR 58,9% · R:R 0,93.

**E l'ultima gamba possibile**: tetto a 3 strategie, DriftPullback viva, VaultBreak chiusa.

## Prima cosa: rifare lo Stage 2 a costi onesti

Il run `ORB_MaxRisk3000_Delta_Cutoff11_IS-intero` usa **$2,50/contratto + 1 tick** (~$10/RT),
il modello leggero. Stessa trappola di VaultBreak. A **$15/RT** l'avg scende da $188,63 a
~$183,63 e il **t da 2,95 a ~2,87**: cambia poco, ma i due numeri devono stare sullo stesso
metro prima di confrontare IS e OOS.

## Attenzione: in ORB **non c'e nessun gate di data nel codice**

Nessun `TradeStartEL`/`TradeEndEL` come in VaultBreak. Quindi **il range del grafico E il
range del backtest**, punto. Ogni run va impostato col Date Range del grafico.

Lead-in richiesto: solo `Max bars back >= 100`, nessuna finestra lunga da riempire.

## Configurazione dei due run

Identica in tutto tranne le date. `@NQ` **5 min**, timezone **Exchange (CT)**, session
template **Globex 24h** (l'IS chiude alle 16:00 CT, verificato dal report), Bar Magnifier
**1 min**, **1 contratto** (`SizingMode 0`), commissione **$7,50/contratto**, slippage **0**.

| run | Date Range del grafico |
|---|---|
| Stage 2 (IS) | 2020-01-01 -> 2024-12-31 |
| Stage 5 (OOS) | 2025-01-01 -> oggi |

## Criteri OOS (Stage 5)

| criterio | soglia |
|---|---|
| **t** | **>= 1,3** |
| WR | >= 50%, e dello stesso ordine del **58,9%** dell'IS |
| R:R | 0,5-1 |
| DD | <= 1,5x quello dell'IS a costi onesti |

**Kill:** `t < 1,3` -> cimitero. Nessun ritocco, nessuna variante di recupero.

## Potenza del test, scritta prima

110 trade/anno su 1,78 anni -> **n atteso ~196**. Con la sd dell'IS ($1.500):

| ipotesi | avg | t a n=196 |
|---|---|---|
| edge intero | $183,63 | **1,71** |
| edge dimezzato | $91,81 | 0,86 |
| come VaultBreak (15%) | $27,54 | 0,26 |

**Anche nel caso migliore ci si aspetta t ~1,7**, non 2,9. La soglia a 1,3 lascia passare solo
un edge che persiste sopra il ~76%. Un edge dimezzato muore.

## Attesa dichiarata sul WR

**56-61%.** Stop e target sono entrambi legati al range di apertura, quindi scalano insieme:
P(primo tocco) = S/(S+T) dipende dal rapporto e non dalla scala -> **WR invariante al regime**,
la regola gia verificata tre volte. Se il WR crolla sotto 50% non e il regime, e che l'edge non
c'era.

## Riserva gia a verbale dallo Stage 4 (29/09), da non dimenticare

Lo split-sample dell'IS diceva: **prima meta 2020-01 -> 2022-06 senza edge** (414 trade, PF
0,999, net -$162), tutto il profitto nella seconda meta. Il filtro delta guadagnava +21% nella
prima meta e **solo +2,5% nella seconda**, cioe dentro il rumore proprio nel periodo recente.

**Quindi l'aspettativa onesta per l'OOS e bassa**, ed e scritta prima di vederlo.

## Stage 2 e Stage 5 — ESITO: NON PASSA l'OOS. Cimitero.

Report: `reports/ORB_S2_IS_nocutoff_costi-onesti.xlsx` e
`reports/ORB_S5_OOS_nocutoff_2025-2026.xlsx`.

### La configurazione girata NON e quella pre-registrata

`UseEntryCutoff` ha ricevuto **11** e `Cutoff_H` **12**: i due valori sono finiti negli input
sbagliati. La riga 130 del codice e `if UseEntryCutoff = 1 and Bar_Time >= Cutoff_Time`, quindi
con 11 la condizione e **sempre falsa** e **il cutoff non si applica mai**.

Entrambi i run sono percio la variante **senza cutoff** (MaxRisk3000 + DeltaFilter), 674 trade
sull'IS — esattamente il run del 29/09. **Ma IS e OOS usano la stessa configurazione**, quindi
sono confrontabili fra loro: quello che si giudica e la variante senza cutoff.

### I numeri

| | **IS 2020-2024** | **OOS 2025-2026** |
|---|---|---|
| n | 674 | **129** |
| avg trade | $151,71 ± 55,31 | **$120,54 ± 150,37** |
| WR | 57,0% | **60,5%** |
| R:R | 0,97 | 0,77 |
| **t** | **2,74** | **0,80** |
| PF | 1,284 | 1,179 |
| frequenza | 0,54 trade/giorno | **0,29** |

Gate 2 superato (t 2,74 · WR 57,0% · R:R 0,97). **Gate 3 no: t = 0,80.**

### Perche il run conta, invece di essere invalidato come i tre di VaultBreak

La tentazione c'e: **n = 129 contro i ~196 pre-registrati**, e a n=129 nemmeno un edge intero
avrebbe raggiunto la soglia (t = 1,01). Sembra lo stesso caso del run VaultBreak a n=71.

**Non lo e, e la differenza e il motivo del campione piccolo.** Li la causa era tecnica: il
grafico non aveva i dati. Qui la frequenza e dimezzata per una **proprieta della strategia nel
nuovo regime**: `MaxRisk_USD 3000` salta i giorni col range di apertura troppo largo, e il
2026 ha ATR 367 contro i 210 del 2020-2024, quindi ne salta molti di piu. **E lo stesso
meccanismo documentato il 29/09** («non e stato escluso l'anno, sono stati saltati i giorni
con range oltre 150 punti»).

Il campione piccolo **e il risultato**, non un difetto della misura. Invalidarlo sarebbe
ragionamento motivato.

### E comunque sarebbe morta allo Stage 7

Indipendentemente dal t: net $15.550 su 1,77 anni = **$878/anno per micro**, contro un target
di $3.000. Sono **3,4 anni con 1 micro**, contro i **7,8 mesi** di DriftPullback. Anche con
l'edge al 100% il conto non si forma.

### Nota onesta: l'edge non e crollato

Avg $120,54 contro $151,71 e il **79%**, e il WR e perfino salito (60,5% contro 57,0%). Non e
il collasso di VaultBreak (15%). **La stima puntuale regge, le prove no**: con 129 trade la
barra d'errore e $150 e non si distingue $120 da zero.

### L'OOS 2025-2026 e speso

Non si rigira con `UseEntryCutoff 1`. Sarebbe scegliere il migliore fra due risultati sugli
stessi dati, cioe esattamente la corruzione che la regola «l'OOS si gira una volta sola»
esiste per impedire. La variante cutoff11 potra essere giudicata solo su dati **non ancora
usati**, e oggi non ce ne sono.

**ORB e chiusa.**

## Rifatto con i parametri giusti: `cutoff11` NON passa. t = 0,63.

Report: `reports/ORB_S2_IS_cutoff11_costi-onesti.xlsx` e
`reports/ORB_S5_OOS_cutoff11_2025-2026.xlsx`. Configurazione verificata: `UseEntryCutoff 1`,
`Cutoff_H 11`, `Cutoff_M 0`, `TP_RR 1.0`, `MaxRisk_USD 3000`, `UseDeltaFilter 1`,
`AllowShort 0`. 550 trade sull'IS, cioe esattamente il conteggio atteso.

### La regola applicata, scritta PRIMA di guardare i numeri

Il primo run era un **errore di esecuzione** (i valori 11 e 12 finiti negli input sbagliati),
non una scelta di variante: la SPEC pre-registrava `cutoff11` prima di vedere qualunque OOS.
Quindi il test pre-registrato non era mai stato eseguito, ed eseguirlo e legittimo. **Ma un
risultato correlato era gia stato visto** (t 0,80 sulla variante senza cutoff, di cui cutoff11
e un sottoinsieme), e quell'informazione non si cancella. Verdetto dichiarato **asimmetrico**:

- **fallisce -> morta, senza ambiguita** (un fallimento dopo uno sguardo non puo essere
  selezione a nostro favore);
- **passa -> provvisorio**, da confermare su dati non ancora usati.

**E fallito.** Quindi il ramo conclusivo.

### I numeri

| | **IS 2020-2024** | **OOS 2025-2026** |
|---|---|---|
| n | 550 | **111** |
| avg trade | $178,97 ± 63,85 | **$108,02 ± 172,29** |
| WR | 58,5% | **59,5%** |
| R:R | 0,93 | 0,78 |
| **t** | **2,80** | **0,63** |
| PF | 1,317 | 1,145 |
| frequenza | 0,438 trade/giorno | **0,247** |

Gate 2 superato (t 2,80, e la stima fatta prima era ~2,87). **Gate 3 no.**

### Le due varianti a confronto: il cutoff peggiora

| variante | IS t | OOS t | edge realizzato | $/anno per micro |
|---|---|---|---|---|
| senza cutoff | 2,74 | **0,80** | 79% | $878 -> 3,4 anni |
| **cutoff11** | 2,80 | **0,63** | **60%** | **$677 -> 4,4 anni** |

Il cutoff delle 11:00 **non ha aiutato fuori campione**, ha peggiorato: t da 0,80 a 0,63 ed
edge dal 79% al 60%. **Conferma la riserva del 29/09**, scritta allora: il filtro guadagnava
+21% nella prima meta dell'IS e **solo +2,5% nella seconda**, dentro il rumore proprio nel
periodo piu recente. Era un adattamento al 2020-2022, e il 2025-2026 lo ha mostrato.

### Lo stesso meccanismo di frequenza, confermato

0,438 -> 0,247 trade/giorno, dimezzata come nella variante senza cutoff. `MaxRisk_USD 3000`
salta i giorni col range di apertura troppo largo, e il 2026 ha ATR 367 contro i 210 del
2020-2024. **Non e un difetto della misura: e la strategia che smette di operare quando il
mercato si allarga.**

### Verdetto

**ORB e chiusa su entrambe le varianti**, entrambe fuori campione, entrambe con la
configurazione verificata dal foglio Settings e i costi onesti. E in ogni caso non sarebbe
arrivata: **4,4 anni per fare $3.000 con 1 micro**, contro i 7,8 mesi di DriftPullback.
