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
