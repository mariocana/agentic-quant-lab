# SPEC — VaultBreak NQ (Stage 0)

**Ipotesi**: quando NQ, in RTH, chiude sopra una "noise boundary" = open di sessione +
0.6 × range giornaliero medio, e sta sopra il VWAP di sessione, il movimento è
direzionale e non rumore; conviene comprarlo e tenerlo finché il VWAP regge.
**Perché**: il range medio giornaliero definisce quanto il prezzo si muove "per caso"
(Larry Williams / Zarattini noise band); superarlo con il VWAP a favore segnala flusso
istituzionale netto in acquisto. Chi perde: chi vende il breakout come esaurimento.
Nel corso: WR ~70% negli ultimi 40 giorni, usato nel basket delle live (pass rate
singola 43%).

| | |
|---|---|
| Famiglia | trend / volatility breakout |
| Strumento · TF · sessione | @NQ · 5 min · **RTH** (08:30–15:00 CT) |
| Noise boundary | `SessOpen + NoiseMult(0.6) × DailyATR`, DailyATR = media **rolling 252 sessioni** del range (versione `10. long rolling ATR`: indipendente dalla data di partenza) |
| Entry | close > NoiseUp **e** close > VWAP di sessione, 08:45–14:00 CT, long only |
| Stop | $2.000 per contratto NQ (100 pt) — `SetStopLoss`, scala con i contratti |
| Target | $1.000 per contratto (50 pt) — R:R nominale 0.5 |
| Altre uscite | 2 chiusure consecutive sotto il VWAP; flat 14:50 CT |
| Trade/giorno | max 3 |
| Profilo prop | R:R 0.5, WR alto → ok. ~~L'uscita VWAP chiude la maggior parte dei trade prima di TP/SL~~ **falso, verificato al Gate 1**: vedi sotto |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: NoiseMult 0.5/0.7 con DailyATRLen 252/504
(ri‑ottimizzare insieme, cluster); MaxTradesPerDay 1 vs 3; TP/SL in punti anziché $.
**Note codice**: template del corso ha gli orari in ET (0945/1500/1550) → su chart CT
usare 0845/1400/1450. `SetStopLoss`/`SetProfitTarget` sono per posizione: con N
contratti moltiplicare. Il DailyATR seeded/expanding del template originale NON si usa.
**Kill**: gate pipeline. Se in OOS il WR scende sotto 55% con R:R 0.5, la strategia non
serve alla prop.

## Gate 1 superato — 01/10/2026

100 giorni (29/06 → 30/09/2026), `DailyATRLen 20` per il lead‑in, costi on, Bar Magnifier
1 min, chart @NQ 5 min su sessione custom **RTH CME 08:30–15:00 CT** (verificata: prima
barra timbrata 08:35).

| Controllo | Esito |
|---|---|
| Stop | **−100,00 pt esatti** su tutti e 9 gli stop |
| Target | **+50,00 pt esatti** su tutti e 25 |
| Peggior trade | −$2.005 = 100 pt × $20 + costi |
| Orari ingresso | 09:00 → 13:55, dentro 08:45–14:00 |
| Uscita a tempo | 14:55 (segnale 14:50 eseguito alla barra dopo) |
| Max ingressi/giorno | 3, mai 4 |
| Overnight | 0 |
| **Scaling ×10** | **esatto su ogni metrica** (net, peggior trade, DD: rapporto 10,000; stesso n, stesso PF) |

Lo scaling era il controllo critico: `SetStopLoss` è **per posizione**, non per contratto,
quindi senza `CurrentContracts` con 10 contratti lo stop varrebbe un decimo.

### Correzione alla spec: l'uscita VWAP è marginale

Distribuzione reale delle uscite: **Profit Target 62% · Stop Loss 22% · VB‑VWAPX 8% ·
VB‑TIMEX 5%**.

Non è un bug — le tre uscite VWAP scattano a −38, −64 e −80 punti dall'ingresso, quindi il
contatore funziona. È che **non fa in tempo**: l'ingresso richiede prezzo sopra `NoiseUp`,
cioè ben sopra l'apertura di sessione, e a quel punto il VWAP di giornata sta spesso più di
100 punti sotto. Lo stop fisso scatta prima.

**Conseguenza**: la strategia è di fatto *«compra il breakout, +50 / −100»*, con R:R 0.5 su
quasi tutti i trade. Non è un male — è il profilo prop — ma le varianti pre‑registrate sul
VWAP contano poco, mentre quelle su **stop e target** contano tutto. Da tenere presente
allo Stage 4.

### Nuovi input `TradeStartEL` / `TradeEndEL`

Non sono logica di trading (default 0 = spenti, comportamento invariato): servono a
separare il **lead‑in** dal periodo valutato, perché in MultiCharts il range del grafico è
anche il range del backtest. Con `DailyATRLen 252` servono 252 sessioni prima dell'IS,
altrimenti il primo anno non produce trade.

Formato data EasyLanguage, `YYYMMDD` con `YYY = anno − 1900`:

| data | valore |
|---|---|
| 01/01/2020 | `1200101` |
| 30/06/2022 | `1220630` |
| 01/07/2022 | `1220701` |
| 31/12/2024 | `1241231` |

Il gate agisce **solo sugli ingressi**: una posizione già aperta resta gestita.

### Osservazione da verificare allo Stage 2

Drawdown **$8.156 in tre mesi** su 39 trade. Per confronto l'ORB, stessa misura, faceva
$15.017 **in cinque anni**. Un massimo su tre mesi non si estrapola, e `DailyATRLen` era a
20 anziché 252 — ma il drawdown su cinque anni può solo essere **maggiore** di quello su
tre mesi. Annotato prima dello Stage 2 per non trasformarlo in una giustificazione dopo.

## Stage 4 — `MaxTradesPerDay 1` bocciata (01/10/2026)

| | avg $ | PF | net $ | DD | **P/D** |
|---|---|---|---|---|---|
| 1ª metà, 3/giorno | 92,02 | 1,202 | 38.186 | −18.895 | 2,02 |
| 1ª metà, **1/giorno** | **234,18** | 1,656 | 50.348 | −10.134 | **4,97** |
| 2ª metà, 3/giorno | 134,58 | 1,308 | 41.450 | −14.509 | 2,86 |
| 2ª metà, **1/giorno** | **81,55** | 1,162 | 13.781 | −12.447 | **1,11** |

Split‑sample: 1ª metà **+154%**, 2ª metà **−39%**. Scartata.

**Da ricordare come caso di studio**: sull'IS intero la variante migliorava avg trade
($110 → $167), PF (1,246 → 1,397) **e** drawdown ($18.895 → $16.317). Tre metriche su tre.
Ma il **P/D peggiorava** (4,21 → 3,93) e tutto il guadagno veniva dalla prima metà.

### Segnale di fragilità

Più grave del fallimento della variante: **il parametro ottimale si ribalta fra le metà**.
2020‑2022 vuole 1 trade/giorno (P/D 4,97 contro 2,02), 2022‑2024 ne vuole 3 (2,86 contro
1,11). Nei rientri dopo uno stop sta il problema in un periodo e il guadagno nell'altro.

Il base case a 3/giorno **maschera** l'instabilità, perché con quel valore le due metà
sembrano coerenti (PF 1,202 e 1,308). Da tenere presente allo Stage 5: è il tipo di
fragilità che emerge fuori campione.

## Stage 4 — prova (b): porting su @ES. Regola di conversione, **decisa prima di lanciare**

Il codice **non cambia**: `StopLossPts` e `TakeProfitPts` sono già in punti, quindi il
porting è un cambio di due input più lo strumento. Tutto il resto resta identico:
`NoiseMult 0.60`, `DailyATRLen 252`, `EarliestEntry 845`, `LatestEntry 1400`,
`FlattenTime 1450`, `MaxTradesPerDay 3`, `VWAPExitBars 2`, sessione **RTH CME custom**.

### Come si converte

Stop e target si riscalano sul **rumore proprio dello strumento**, cioè sul `DailyATR` che
la strategia già calcola. Rapporto letto da `ShowLog`, 21 campioni trimestrali sull'IS:

| data | ATR @NQ | ATR @ES | ES/NQ | | data | ATR @NQ | ATR @ES | ES/NQ |
|---|---|---|---|---|---|---|---|---|
| 02/01/20 | 81,71 | 28,42 | 0,348 | | 03/01/23 | 303,07 | 78,05 | 0,258 |
| 01/04/20 | 118,27 | 45,47 | 0,384 | | 03/04/23 | 268,81 | 70,34 | 0,262 |
| 01/07/20 | 145,36 | 57,32 | 0,394 | | 03/07/23 | 228,90 | 60,96 | 0,266 |
| 01/10/20 | 176,62 | 65,21 | 0,369 | | 02/10/23 | 212,99 | 48,79 | 0,229 |
| 04/01/21 | 206,85 | 66,08 | 0,319 | | 02/01/24 | 196,27 | 43,57 | 0,222 |
| 01/04/21 | 204,66 | 53,66 | 0,262 | | 01/04/24 | 188,94 | 41,75 | 0,221 |
| 01/07/21 | 199,81 | 48,45 | 0,242 | | 01/07/24 | 199,87 | 45,35 | 0,227 |
| 01/10/21 | 181,40 | 42,87 | 0,236 | | 01/10/24 | 227,23 | 51,29 | 0,226 |
| 03/01/22 | 192,26 | 42,88 | 0,223 | | 31/12/24 | 244,08 | 55,50 | 0,227 |
| 01/04/22 | 230,15 | 58,37 | 0,254 | | | | | |
| 01/07/22 | 275,75 | 75,14 | 0,272 | | **media** | **208,66** | **55,26** | **0,2648** |
| 03/10/22 | 298,80 | 81,09 | 0,271 | | | | | |

**Fattore adottato: 0,265** (rapporto delle medie, non media dei rapporti — pesa i periodi
per la loro volatilità assoluta, che è ciò che conta per uno stop fisso).

| | @NQ | @ES |
|---|---|---|
| `StopLossPts` | 100 | **26,50** |
| `TakeProfitPts` | 50 | **13,25** |
| Stop in $ (mini) | $2.000 | $1.325 |
| Target in $ (mini) | $1.000 | $662,50 |
| Stop in $ (micro) | $200 | **$132,50** |
| Target in $ (micro) | $100 | $66,25 |

Entrambi i valori ES sono multipli di 0,25 (tick), quindi rappresentabili esatti.

### Due avvertenze messe per iscritto **prima** dei risultati

**1. Il rapporto non è stabile.** È passato da 0,35 (2020) a 0,22 (2024): NQ ha guadagnato
volatilità relativa su ES per cinque anni di fila. Uno stop fisso a 0,265 sarà quindi
**troppo stretto** nella prima metà dell'IS e **troppo largo** nella seconda. È lo stesso
difetto che ha già il 100 fisso su NQ — per questo lo teniamo uguale, per confrontare like
for like — ma se ES dovesse mostrare uno split‑sample sbilanciato, **questa è la prima
spiegazione da considerare**, prima di concludere che lo strumento non funziona. La cura
(stop in frazioni di `DailyATR` anziché in punti) è una variante separata, non ora.

**2. ES parte con un handicap di attrito di ~3×.** Il tick ES vale $12,50 contro i $5,00 di
NQ, ma l'ATR di ES vale ~220 tick contro gli ~836 di NQ: rispetto al proprio rumore, ES è
uno strumento **4 volte più grossolano**.

| | @NQ | @ES |
|---|---|---|
| Commissioni r/t (mini) | $3,50 | ~$3,50 |
| Slippage 2 tick | $10,00 | $25,00 |
| **Attrito totale** | **$13,50** | **$28,50** |
| in % del target | 1,35% | **4,30%** |

Quindi se ES esce peggio di NQ di un margine modesto, **non è una bocciatura della logica**:
è il costo. Se esce meglio *nonostante* questo, il segnale è forte.

### Metro di giudizio

**P/D**, come da `pipeline_prop.md`. Riferimento da battere: **4,21** (NQ, IS intero).
Tre run come sempre: IS intero + due metà. La variante passa solo se il P/D migliora **e**
lo split‑sample non si ribalta.

**Aspettativa dichiarata**: l'attrito relativo 3× dice che ES dovrebbe uscire *peggio* sul
P/D. Il motivo per provarlo comunque è la **granularità**: $132,50 di rischio per micro
contro $200 significa poter tenere ~1,5× i contratti sotto lo stesso MLL di $2.000, e la
size è l'unico modo per arrivare a $3.000 di target quando il P/D è appena sufficiente.

### Costi: identici a tutti i run precedenti

Letti dai report esistenti (`Settings` dell'xlsx), **non li cambiamo**, altrimenti il
confronto con NQ non vale:

| | |
|---|---|
| Commission | **`2.5$ per Contract`** (per lato) |
| Slippage | **`1 tick`** — MultiCharts lo esprime in tick, si converte da solo |
| Bar Magnifier | **Enabled, 1 Minute** |
| Interest Rate | 0.02 |

$2,50/lato è più conservativo della tariffa Lucid reale su NQ ($1,75). La tariffa ES/MES
non è ancora a verbale: si corregge allo Stage 7.

### ⚠ Lo slippage non viene quasi addebitato — correzione analitica obbligatoria

Verificato sui report: con `Slippage 1 tick` impostato, MultiCharts ha addebitato

| run | trade | slippage teorico (1 tick × 2 lati) | **addebitato** | % |
|---|---|---|---|---|
| VB Stage 2 IS intero | 723 | $7.230 | **$213,80** | 3,0% |
| ORB IS 2020‑24 costi | 827 | $8.270 | **$292,80** | 3,5% |

Causa probabile (**da verificare**): MC limita lo slippage al range della barra, e con il
Bar Magnifier su 1 minuto molte barre valgono 1–2 tick, quindi non c'è spazio per
applicarlo. Qualunque sia il meccanismo, il fatto è che **tutti i nostri numeri di Stage 2
sono ottimistici dello slippage quasi intero**.

Effetto su VaultBreak NQ:

| ipotesi di slippage | costo | net | **P/D** |
|---|---|---|---|
| come da backtest | $214 | 79.636 | **4,21** |
| 1 tick su entry + 1 tick sui soli stop (22%) | $4.410 | 75.440 | **3,99** |
| 1 tick su entrambi i lati | $7.230 | 72.620 | **3,84** |

Nello scenario pieno **scende sotto la soglia MC‑robusta di 3,86**. Il margine che sembrava
esistere è in buona parte slippage non pagato.

**Perché questo è decisivo proprio per ES**: il tick ES vale $12,50 contro $5,00. Se ES
producesse un numero di trade simile (~700), lo slippage pieno sarebbe **~$17.500** contro
i ~$7.200 di NQ, su un gross stimato di ~$51.000 (avg trade ≈ $110 × 0,6625, stima). Cioè
**~34% del gross contro l'8% di NQ** — esattamente l'handicap 4× previsto sopra, che però
**il backtest non mostrerà**, perché lo slippage non lo addebita.

**Regola per questo confronto**: si tengono le impostazioni invariate (comparabilità) e si
applica la correzione **a posteriori e allo stesso modo sui due strumenti**, dal numero di
trade del report:

```
slippage_reale = n_trade × 2 × tick_value      (NQ $5,00 · ES $12,50)
net_corretto   = net_report − slippage_reale + slippage_addebitato
P/D            = net_corretto / drawdown
```

Il P/D si legge **su net_corretto**, non su quello del report. Il riferimento NQ da battere
diventa quindi **3,84** (scenario pieno), non 4,21.

> **Da aprire come voce separata**: rifare i Gate 2/3 già passati con lo slippage incorporato
> nella commissione (`$2,50 + 1 tick = $7,50 per contratto per lato` su NQ) invece che come
> campo slippage. Non ora: prima si chiude la prova ES a parità di condizioni.

## Stage 4 — prova (b) **bocciata**: @ES è nettamente peggiore (01/10/2026)

Setup verificato dai report: `@ES`, `StopLossPts 26.5`, `TakeProfitPts 13.25`, `NoiseMult
0.60`, `DailyATRLen 252`, `MaxTradesPerDay 3`, date `1200101/1220630/1220701/1241231`,
costi `2.5$ per Contract` + `1 tick` + Bar Magnifier 1 min. Tutto come pre‑registrato.

| | net | n | avg | DD | **P/D** | P/D slip. reale | P/D slip. pieno |
|---|---|---|---|---|---|---|---|
| **NQ** IS intero | 79.636 | 723 | 110,15 | −18.895 | **4,21** | 3,94 | 3,84 |
| NQ 1ª metà | 38.186 | 415 | 92,02 | −18.895 | 2,02 | 1,87 | 1,81 |
| NQ 2ª metà | 41.450 | 308 | 134,58 | −14.509 | 2,86 | 2,71 | 2,65 |
| **ES** IS intero | 29.248 | 576 | 50,78 | −12.094 | **2,42** | **1,56** | **1,26** |
| ES 1ª metà | 15.118 | 336 | 45,00 | −12.094 | 1,25 | 0,75 | 0,58 |
| ES 2ª metà | 14.129 | 240 | 58,87 | −9.470 | 1,49 | 1,03 | 0,88 |

*Slippage reale* = 1 tick su entry + su tutte le uscite **tranne il Profit Target** (limit,
non slitta): NQ 1.069 fill, ES 870. *Pieno* = 1 tick su entrambi i lati.
Uscite: NQ TP 377 / TIMEX 161 / SL 100 / VWAPX 85 · ES TP 282 / TIMEX 134 / VWAPX 87 / SL 73.

**Bocciata su tutti e tre i run, in ogni scenario di costo.** Corretto, ES scende a **1,26**
contro la soglia `Target/MLL = 1,50` del 50k: non passa nemmeno il criterio di fattibilità,
prima ancora del Monte Carlo.

### Non è (solo) l'attrito: l'edge su ES è più debole

| | gross/trade | stop | **edge in R** |
|---|---|---|---|
| NQ | $115,44 | $2.000 | **0,0577** |
| ES | $56,53 | $1.325 | **0,0427** |

A parità di rischio, ES rende il **26% in meno prima dei costi**. Il ridimensionamento ATR
funziona (lo stop ES è il 66% di quello NQ, l'avg trade è il 49%): è proprio il vantaggio
per unità di rischio che è inferiore. Poi arriva l'attrito e finisce il lavoro — lo
slippage pieno vale **44% del gross** su ES contro l'**8,7%** di NQ.

### Le due avvertenze pre‑registrate: verificate, e non salvano la variante

1. **Il drift del rapporto ATR ha morso davvero.** La prima metà — dove 0,265 rende lo stop
   troppo stretto per ES — è la peggiore (P/D 1,25 contro 1,49). Direzione esatta prevista.
   Ma anche la metà "favorita" resta sotto NQ (1,49 vs 2,86) e sotto 1,50 una volta corretta.
2. **L'handicap di attrito era sottostimato**: avevo previsto ~34% del gross, è il 44%.
   Avevo stimato l'avg trade lordo ES a ~$73, è $56,53.

**Split‑sample coerente**: entrambe le metà peggiori di NQ, nessun ribaltamento. È un
risultato pulito, non il caso di un singolo periodo.

### La granularità c'era — e non è bastata

L'ipotesi era giusta sul rischio: per micro, DD **MES $1.209** contro **MNQ $1.889** su un
MLL di $2.000. Ma crolla il profitto: per micro, net corretto **$1.528** (ES) contro
**$7.262** (NQ). Test di fattibilità su MES: servono `N ≥ 3.000/1.528 = 2` contratti per il
target e `N ≤ 2.000/1.209 = 1` per l'MLL. **Nessuna N valida.**

### Cosa questo NON dice

Boccia **«VaultBreak su ES con parametri ATR‑equivalenti»**, non «ES». Esiste in teoria uno
stop ES migliore del 26,5 — ma cercarlo dopo aver visto questi numeri è curve fitting sullo
strumento, ed è esattamente ciò che la regola pre‑registrata serviva a impedire. Se mai si
riaprisse, è una **nuova spec Stage 0**, non una variante di questa.

**Conseguenza sulla pipeline**: la strada (b) del 01/10 — «strumento meno volatile in
dollari» — è chiusa per VaultBreak. Restano la (a) rischio per trade (già bocciata con
`MaxTradesPerDay 1`) e la griglia `NoiseMult` × `DailyATRLen`, l'ultima pre‑registrata.

## Stage 2 rifatto con i costi onesti — baseline per il Gate 3 (01/10/2026)

`Commission 7.5$ per Contract` ($2,50 + 1 tick da $5,00), `Slippage 0 ticks`, tutto il resto
identico. Controprova che il cambio è solo di costo: **723 trade** e stessa distribuzione
delle uscite (TP 377 · TIMEX 161 · SL 100 · VWAPX 85) del run precedente.

| | slippage 1 tick (sottostimato) | **costi onesti** |
|---|---|---|
| Net profit | 79.636 | **72.620** |
| Costi totali | 3.829 | **10.845** |
| Avg trade | 110,15 | **100,44** |
| Profit Factor | 1,246 | **1,220** |
| Max Strategy DD | −18.895 | **−19.113** |
| Max Close‑to‑Close DD | −18.368 | −18.620 |
| **P/D** | 4,21 | **3,80** |

Il net coincide al dollaro con la correzione analitica prevista ($72.620): il metodo era
giusto. **Questo è il report di input del Gate 3**, non il precedente.

- **Gate 2** con i costi veri: DD/10 = **$1.911** per micro contro la soglia $1.000. Resta
  fallito (era già passato per waiver registrato).
- **P/D 3,80** contro la soglia MC‑robusta stimata 3,86: sotto, ma di un'incollatura. La
  stima non decide — decide il Monte Carlo.
- Se il rapporto 2,57× misurato sull'ORB si ripetesse, il 95° percentile uscirebbe a
  ~$49.100, cioè **$4.912 per micro** contro un MLL di $2.000. Previsione scritta prima del
  run: **VaultBreak non passa il Gate 3**. Se passa, il 2,57× non è una costante e va
  ricalibrato.

## Gate 3 **fallito** — VaultBreak chiusa (01/10/2026)

Monte Carlo 1000 reshuffle, 100% dei trade, sul report a costi onesti.

| | |
|---|---|
| Base (close‑to‑close) | −$18.620 |
| Mediana (50°) | −$18.105 |
| **95° percentile** | **−$31.090** |
| Largest drawdown su 1000 | −$39.945 |
| **Per micro** | **$3.109** contro un MLL di **$2.000** |

**Sforo del 55%. Gate 3 fallito.** Mediana net profit positiva e nessun problema sul lato
profitto: è il drawdown della coda, esattamente come per l'ORB.

### Il numero che conta più del verdetto

| | DD storico (c2c) | 95° perc. | per micro |
|---|---|---|---|
| ORB (dopo 3 varianti) | $12.184 | $31.210 | **$3.121** |
| VaultBreak (base case) | $18.620 | $31.090 | **$3.109** |

Due strategie **indipendenti** — logica diversa, trigger diverso, numero di trade diverso,
una ottimizzata in tre passaggi e l'altra no — finiscono a **$3.109 e $3.121 per micro**.
Uno scarto dello 0,4%. Non è una coincidenza sulle singole strategie: è la misura di quanto
costa, in coda, tenere 1 micro NQ in un breakout long‑only intraday.

### Previsione sbagliata, e ricalibrazione

Avevo previsto ~$49.100 applicando il 2,57× dell'ORB. **Sbagliato: è uscito $31.090**, cioè
un rapporto di **1,67×**. Il fattore di amplificazione del Monte Carlo **non è una costante**:
dipende dalla dispersione dei trade. L'ORB aveva perdite fino a $3.000 (cap `MaxRisk_USD`) ed
è molto più sensibile al reshuffle; VaultBreak ha la perdita bloccata a −$2.015 e una
distribuzione più regolare. La regola derivata «P/D ≥ 3,86» è ritirata da `pipeline_prop.md`.

### Perché il criterio P/D da solo non bastava

P/D sulla coda MC = 72.620 / 31.090 = **2,34 ≥ 1,50**: il criterio di fattibilità **passa**.
Ma richiede `N ≥ 3.000/7.262 = 0,41` e `N ≤ 2.000/3.109 = 0,64` micro — e **mezzo micro non
esiste**. È la condizione di granularità che manca al criterio, ora aggiunta alla pipeline.

### Kill

La spec diceva: «gate pipeline». Il gate è fallito. **VaultBreak si chiude come l'ORB**, e
la griglia `NoiseMult` × `DailyATRLen` **non si lancia**: sarebbe la quarta variante su una
strategia già bocciata, lo stesso errore fatto sull'ORB.

Quel che resta — e va usato, non riscritto da zero: il codice è corretto e verificato al
Gate 1, gli input `TradeStartEL`/`TradeEndEL` servono a tutte, e la lezione sul rischio per
micro vale per l'intera famiglia.

---

# Stage 5 — OOS 2025‑2026: pre‑registrazione (15/10/2026, prima del run)

Riaperta dalla pipeline semplificata del 15/10: il Gate 3 che l'aveva uccisa (DD 95° pct
÷10 ≤ $2.000) era **nostro**, non del corso, ed è stato ritirato. VaultBreak è l'unica delle
sei a passare il Gate 2 nuovo: **t = 2,63** e **avg trade $110** sull'IS.

**L'OOS non è mai stato eseguito**, perché moriva prima.

## Il riferimento IS (2020‑2024)

n = 723 (145/anno) · avg **$110** · sd $1.124 · WR **63,1%** · PF **1,246** · R:R 0,730 ·
**t = 2,63** · DD $18.895

## Il run

| | |
|---|---|
| Chart | @NQ 5 min, sessione **RTH CME custom 08:30–15:00 CT**, Bar Magnifier 1 min |
| **Range del chart** | **dal 2024‑01‑01** (serve il lead‑in: `DailyATRLen 252`) **a oggi** |
| **`TradeStartEL`** | **1250101** |
| **`TradeEndEL`** | **1261015** |
| Input | `NoiseMult 0.60` · `DailyATRLen 252` · `EarliestEntry 845` · `LatestEntry 1400` · `FlattenTime 1450` · `MaxTradesPerDay 3` · `VWAPExitBars 2` · `StopLossPts 100` · `TakeProfitPts 50` · `Num_Contracts 1` |
| Costi | commissione **$2,50/contratto** + slippage **1 tick** (= i nostri $7,50/lato) |

**Identici allo Stage 2.** Il range del chart parte un anno prima della finestra valutata
perché `TradeStartEL`/`TradeEndEL` separano il lead‑in dal periodo misurato.

## Le soglie, e perché non sono quelle del Gate 2

L'OOS è **1,79 anni ≈ 258 trade attesi**. Con l'edge IS identico, l'errore standard è $70 e
il **t atteso è 1,57**: la soglia `t ≥ 2` boccerebbe un edge **intatto** due volte su tre.

| criterio | se l'edge è intatto | se l'edge è zero |
|---|---|---|
| ~~t ≥ 2~~ | 33% | 2% |
| **t ≥ 1,3** | **61%** | **10%** |
| **avg trade ≥ $70** | **72%** | **16%** |

**`t ≥ 1,3` è il livello del corso** («maximum of 10% of the simulations being unprofitable»
= 10% di falsi positivi). Non è un'asticella abbassata: è quella giusta per questo campione.

### Passa se, tutte:

1. **avg trade ≥ $70**
2. **t ≥ 1,3**
3. **WR ≥ 50%** (IS: 63,1%)
4. **PF e R:R dello stesso ordine dell'IS** (1,246 e 0,730)
5. **DD ≤ 1,5 × IS**, cioè ≤ **$28.343**

### Se passa

Si va allo **Stage 7**, dove il livello di rischio è un output: si cerca quello che massimizza
il pass rate entro i vincoli (pass ≥ 40% al 1°, ≥ 85% in 4, ≤ 15 giorni, consistenza 50%).
Il pass rate in‑sample a $120 per trade era **90%**; sull'OOS va rifatto da zero.

### Se non passa

**Cimitero, definitivo.** E il trigger sul Gate 3 si disarma: significherebbe che il gate
vietava qualcosa che non esisteva comunque.

## Risultato dell'OOS — **fallito. Cimitero definitivo.** (15/10/2026)

295 trade, 2025‑01‑03 → 2026‑10‑05. Report `reports/VB_S5_OOS_2025-2026.xlsx`.
Configurazione identica allo Stage 2, costi equivalenti ($7,50/lato).

| criterio pre‑registrato | soglia | misurato | |
|---|---|---|---|
| 1. avg trade | ≥ $70 | **−$2** | ❌ |
| 2. **t** | ≥ 1,30 | **−0,03** | ❌ |
| 3. WR | ≥ 50% | 62,4% | ✅ |
| 4a. PF | ~1,246 | **0,997** | ❌ |
| 4b. R:R | ~0,730 | 0,601 | ✅ |
| 5. DD | ≤ $28.343 | $20.655 | ✅ |

**Net −$560 su 295 trade.** L'edge fuori campione non è ridotto: è **esattamente zero**
(t = −0,03). 2025: −$4.225 · 2026: +$3.665.

### Il meccanismo: non è il win rate

| | IS | OOS |
|---|---|---|
| WR | 63,1% | **62,4%** — tenuto |
| R:R | 0,730 | **0,601** — **−18%** |

Con R:R 0,601 il WR di pareggio è **62,5%**, e l'osservato è **62,4%**. Le vincite si sono
rimpicciolite del 18% rispetto alle perdite, **quel tanto che basta** a portare il PF a 1,0.

È lo stesso difetto misurato su DriftPullback e su Gold: **il R:R realizzato non è una
costante della strategia.** Qui è bastato un calo del 18% per azzerare tutto.

# ✉️ Chiusa — cimitero, causa **A** (edge assente fuori campione)

L'IS dava t = 2,63 e avg $110. Ma l'IS è anche il periodo su cui è passata per lo **Stage 4**
(tre varianti ottimizzate). Il t di 2,63 misurava, almeno in parte, quell'ottimizzazione.

### Il trigger sul Gate 3 si disarma — era pre‑registrato

La pre‑registrazione diceva: *«Se non passa: cimitero definitivo. E il trigger sul Gate 3 si
disarma: significherebbe che il gate vietava qualcosa che non esisteva comunque.»*

**È esattamente quello che è successo.** Il Gate 3 — che abbiamo passato una giornata a
smontare, con ragione sul piano logico — vietava una strategia **senza edge fuori campione**.

**Ragionamento sbagliato, verdetto giusto.** Vale la pena tenerlo scritto così.
