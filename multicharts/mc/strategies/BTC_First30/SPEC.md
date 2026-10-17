# SPEC — BTC First30 Short (Stage 0)

**Ipotesi**: se i primi 30 minuti della sessione cash USA (08:30–09:00 CT) chiudono in
negativo su Bitcoin, il ribasso prosegue fino alle 15:00 CT; si va short e si tiene fino
alle 15:00.
**Perché**: il retail su BTC è strutturalmente long, quindi gli acquisti del mattino sono
FOMO che il mercato assorbe e poi riporta indietro. Le vendite del mattino invece vanno
contro quel flusso: sono rare e più probabilmente informate o istituzionali, e continuano
per il resto della seduta (nostra ipotesi in più: apertura dei desk USA e flussi degli ETF
spot, che scambiano in quell'orario). Chi perde: chi
compra il ribasso del mattino. Fonte: vincitore Strategy of the Month settembre 2026
(@adri27): net profit +$25.000, PF 1,91, Sharpe 3, **periodo e contratto non dichiarati**.
È un vincitore scelto fra molti concorrenti: per noi è un candidato da validare, non un
risultato (come GAR, dove il WR dichiarato non si è riprodotto).
**Ruolo nel basket**: **short reale** (la funzione che aveva First5, morta per causa B) su
**un altro asset**, con orario 09:00–15:00 CT diverso da GAR (flat alle 10:00 CT).

| | |
|---|---|
| Famiglia | momentum / drift intraday, solo short |
| Strumento · TF · sessione | **@BTC** (sviluppo, 5 BTC, $5/pt) → **MBT** (0,1 BTC, $0,10/pt) · **5 min** · sessione Globex 24h, chart CT |
| Finestra di misura | barre che chiudono 08:35 → **09:00 CT**: `orOpen` = open delle 08:30, `orClose` = close delle 09:00 |
| Entry | `orClose < orOpen` → **short** `next bar at market` (riempie alle 09:00) |
| Exit | prima barra con Time ≥ **15:00 CT** → `next bar at market` (riempie alle 15:00) |
| Stop | **variante B, caso base prop**: massimo della finestra 08:30–09:00 (`StopMode 1`). Variante A originale: nessuno |
| Target | nessuno (`TP_RR 0`); varianti in R allo Stage 4 |
| Giorni | solo **lunedì–venerdì** (se il CME ha attivato il 24/7 sulle crypto, il codice esclude sabato e domenica) |
| Trade/giorno | 1 |
| Guardrail | `MaxRiskPts 4000`: salta il giorno se lo stop è più lontano di 4.000 pt dall'ingresso |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Nota sull'OOS**: la strategia è stata pubblicata a settembre 2026 e il suo autore l'ha
scelta guardando dati che probabilmente coprono anche il nostro OOS. Il nostro OOS è pulito
per noi, non per l'autore. L'unico dato davvero mai visto parte da **ottobre 2026** (paper o
live): lo si tiene come controllo finale, non come gate.

## Conto: da definire — **LucidFlex non è possibile**

Lucid non offre prodotti crypto: lo dice la sua FAQ, e un blog di settore elenca BTC e MBT
fra le esclusioni (verificato 17/10/2026; la lista prodotti ufficiale nell'Help Center non
l'ho letta). La strategia **non può entrare
nello Stage 7 su LucidFlex**. Serve un conto che ammetta **MBT e l'automazione**: da
scegliere e verificare (regole scritte, non forum) **prima dello Stage 7**. Se non se ne
trova uno, la strategia vale solo per capitale proprio.

Fino ad allora le soglie dei gate restano quelle di **LucidFlex 50k** (Target $3.000, MLL
$2.000), usate come metro, per poter confrontare BTC First30 con le altre strategie della
pipeline. Quando il conto è scelto si ricalcolano dal suo Target/MLL.

## Unità: ÷50, non ÷10

Le soglie della pipeline sono "per micro". Su NQ un mini vale 10 micro; qui **un @BTC vale
50 MBT** (5 BTC contro 0,1 BTC). Ogni soglia "÷10" della pipeline diventa **÷50**.

| Soglia (LucidFlex 50k) | per MBT | nel report @BTC (×50) |
|---|---|---|
| Gate 2 — max DD ≤ 50% MLL | ≤ $1.000 | ≤ **$50.000** |
| Gate 2 — peggior trade ≤ 25% MLL | ≤ $500 | ≤ **$25.000** |
| Gate 2 — avg trade netto | ≥ $10 | ≥ **$500** |
| Gate 3 — DD 95° perc. Monte Carlo ≤ MLL | ≤ $2.000 | ≤ **$100.000** |

L'avg trade minimo ($10 per MBT) è una scelta di questa spec: sopra il costo di andata e
ritorno di un MBT (~$7, vedi costi) con margine per un errore di stima dei costi.

## Costi: in micro, non del contratto pieno

Si sviluppa su @BTC per avere lo storico dal 2020 (MBT esiste solo da maggio 2021), ma si
opererà in MBT, dove il costo **per bitcoin** è molto più alto. Lo stesso problema che la
pipeline segnala per MNQ (costo quasi triplo) qui è più grave, perché le fee CME sono per
contratto e un @BTC copre 50 MBT. Quindi il report @BTC si produce **con i costi di 50 MBT**:

- costo per MBT per lato: **$3,00 di commissioni + 1 tick di slippage ($0,50) = $3,50**
  (stima, **da verificare** sulla tabella commissioni del conto scelto e sul fee schedule
  CME);
- in MultiCharts, come da regola dello Stage 2: commissione **`175$ per Contract`**
  (= 50 × $3,50), campo slippage **`0 ticks`**.

Se i costi veri risultano diversi, si rifà il report: costano un run, non una decisione.

## Worst day strutturale

- **Variante A (senza stop)**: non limitato. BTC si muove anche del 10% in una seduta: a
  $100.000 sono $1.000 per MBT in un giorno, metà dell'MLL. **Non deployabile.** Serve solo
  come benchmark: è la strategia originale.
- **Variante B (stop al massimo della finestra + `MaxRiskPts 4000`)**: la perdita massima
  per costruzione è 4.000 pt × $0,10 = **$400 per MBT**, più ~$7 di costi e lo slippage
  oltre lo stop in un movimento veloce. Il valore 4.000 viene dalla soglia del peggior trade
  (≤ $500 per MBT), lasciando ~$90 per costi e slittamento. Durante la sessione USA BTC
  scambia in continuo, quindi non ci sono gap di riapertura fra ingresso e uscita.
- Un trade al giorno: worst day = worst trade.

Il guardrail esiste per la regola della pipeline "si sceglie dalle regole del conto, non
dalla curva". Quanti giorni salta lo si misura allo Stage 1 (distribuzione del rischio nel
log `B30 OR`); se ne salta più del 20%, è un dato da riportare, non un motivo per alzarlo.

## Varianti pre‑registrate (Stage 4)

1. **TP in R** (`TP_RR` 0,5 / 1,0): il profilo prop vuole WR ≥ 55% e R:R 0,5–1. Con
   l'uscita a tempo il WR atteso è vicino al 50%: il target è il modo di portarlo sopra.
2. **Stop**: `StopBufTicks` 0 / 10 sopra il massimo; `StopMode 2` con `StopPts` fisso come
   alternativa allo stop strutturale.
3. **Soglia sul calo** (`MinDropPts` > 0): entra solo se la finestra chiude in negativo di
   almeno N punti. Da esprimere in punti, **non in percentuale**: il continuo è
   back‑adjusted con roll mensili, quindi le percentuali sono distorte.
4. **Lato long come controllo** (`TradeLongs 1`, `TradeShorts 0`): **non è una variante da
   adottare, è il test dell'ipotesi.** La tesi dice che i rialzi del mattino sono rumore. Se
   il lato long rende quanto lo short, la ragione "retail long‑bias" è falsa e resta un
   effetto di momentum generico, da trattare come tale (e già visto morire su NQ).

## Note

- **Roll**: i futures BTC sono **mensili**. La posizione è intraday (09:00 → 15:00), quindi
  non attraversa i roll; il back‑adjustment sposta i livelli ma non le distanze in punti.
  Conseguenza: tutto ciò che è in punti è corretto, tutto ciò che è in percentuale no.
- **Scala dei prezzi**: BTC è passato da ~$7.000 (inizio 2020) a oltre $100.000. Rischio e
  P&L in dollari crescono con il prezzo, quindi nella tabella annuale gli anni recenti
  pesano per forza di più. La regola "nessun anno > 50% del profitto" va letta **anche in
  R** (P&L ÷ rischio del trade), dove la scala sparisce. Se passa in R e fallisce in $, lo
  si scrive e si decide allo Stage 2.
- **Festività USA**: senza mercato cash la "sessione USA" non esiste. Allo Stage 1 si
  elencano i trade nei giorni di festività USA (Thanksgiving, 4 luglio…) e nelle giornate
  a orario ridotto del CME.
- **Basket (Stage 8)**: uno short BTC aperto mentre un'altra strategia è long NQ su un
  altro conto è una coppia correlata. Va guardata con la regola "mai posizioni opposte su
  strumenti correlati".
- **Simbolo TradeStation**: @BTC per lo sviluppo; per il micro verificare in QuoteManager
  il simbolo esatto (@MBT) e che lo storico parta da maggio 2021.

**Kill**: gate della pipeline. In più, kill specifico se con lo stop strutturale (variante
B) l'avg trade netto scende sotto $10 per MBT, oppure se il lato long rende quanto lo short
(l'ipotesi è falsa).

---

# Stage 2 — **Gate 2 fallito** (17/10/2026) → **cimitero, causa A — edge assente**

IS 2020‑01‑07 → 2024‑12‑31, @BTC 5 min, $175/lato (costi da 50 MBT), Bar Magnifier 1 min.
Report in `reports/B30_S2_*_IS.xlsx`. Il corpo sopra è la pre‑registrazione e non si
riscrive.

| run | n | WR | avg netto | per MBT | PF | t | DD chiusi | peggior trade |
|---|---|---|---|---|---|---|---|---|
| A short, senza stop | 643 | 41,5% | −$242 | −$4,84 | 0,85 | −1,34 | $211.225 | −$16.925 |
| **C short, stop (caso base)** | 643 | 28,8% | **−$49** | −$0,99 | 0,955 | −0,38 | $90.850 | −$9.475 |
| D short, stop + TP 1R | 643 | 40,1% | −$298 | −$5,97 | 0,66 | **−3,82** | $216.450 | −$9.475 |
| **LONG** (controllo), stop | 605 | 26,4% | −$175 | −$3,50 | 0,85 | −1,28 | $123.850 | −$10.250 |

**Gate 2 sul caso base C**: n ✅ (643). Avg netto ❌ (−$49 contro ≥ $500). PF ❌ (0,955 contro
1,2). WR ❌ (28,8% contro 55%). R:R ❌ (2,36, fuori da 0,5–1). Max DD ❌ ($90.850 contro
$50.000, cioè **$1.817 per MBT**). Peggior trade ✅ ($9.475 = $190 per MBT). Annuale ❌ (net
negativo). Sei soglie su otto mancate.

### Perché: prima dei costi c'è poco, e non è quello che dice l'ipotesi

Lordo = netto + $350 di andata e ritorno. In punti base del prezzo, per togliere l'effetto
della crescita di BTC (il continuo è back‑adjusted: il minimo del 2020 è a 30.605, quindi
nei primi anni i bp sono sottostimati):

| run | lordo per trade | t lordo | lordo in bp | per anno, bp (2020 → 2024) |
|---|---|---|---|---|
| C short | +$301 | 2,30 | +7,5 | −2,3 · +3,2 · +17,4 · +5,5 · +12,4 |
| LONG | +$175 | 1,28 | +7,3 | +2,4 · +1,6 · +10,1 · +14,5 · +8,5 |
| A short senza stop | +$108 | 0,60 | +1,3 | — |
| D short + TP 1R | +$52 | 0,66 | +0,3 | — |

Il costo mediano di un trade in micro vale **12,8 bp**: più del lordo di qualunque variante.

1. **L'ipotesi è falsa.** Il lato long, misurato come controllo, rende **lo stesso** dello
   short al lordo (+7,3 bp contro +7,5). La tesi "i ribassi del mattino sono informati, i
   rialzi sono FOMO" chiedeva un'asimmetria che non c'è. È il kill pre‑registrato.
2. **Quel poco viene dallo stop, non dal segnale.** Senza stop lo short lordo è +1,3 bp,
   con lo stop all'estremo della finestra +7,5: lo stop taglia le perdite e lascia correre
   pochi trade grandi (WR 29%, R:R 2,4). È lo stesso effetto per long e short: una
   proprietà della forma dell'uscita, non della direzione del mattino.
3. **Il profilo prop lo distrugge.** Il target 1R, l'unico modo per portare il WR verso il
   55%, taglia proprio quei trade: D è a +0,3 bp lordi e t −3,82 netto.
4. **Nemmeno a costi zero si arriva alla soglia.** L'avg minimo è $10 per MBT, il lordo di C
   è $6 per MBT. Senza costi C sarebbe positiva ma sotto soglia, e con un WR del 29% fuori
   dal profilo.

**Causa A, non B.** Il rischio per micro passa (peggior trade $190 per MBT, worst day di spec
$400): il muro di @NQ qui non c'è. Manca l'edge.

**Sul risultato dichiarato dall'autore** (PF 1,91, Sharpe 3): non si riproduce né nell'IS
2020–2024 (PF 0,85 senza stop) né nei quattro mesi dello Stage 1 (PF 0,49). Il periodo e il
contratto non erano dichiarati, quindi non si può dire dove stia la differenza.

**Cosa la riaprirebbe** (regola del cimitero):
- su **@BTC pieno con capitale proprio** il costo per BTC è molto più basso che in micro, ma
  il lordo resta +7,5 bp con t 2,0 su cinque anni, e l'effetto non è quello dell'ipotesi:
  sarebbe una **nuova Stage 0** sull'effetto "stop all'estremo della prima mezz'ora", long e
  short insieme, non una riapertura di questa;
- nessuna variante pre‑registrata dello Stage 4 tocca il problema: `MinDropPts` e il buffer
  dello stop non creano l'asimmetria che manca, e i target in R peggiorano.
