# Go-live di DriftPullback su LucidFlex 50k

Fonti: Lesson 10 del corso (*Automate Execution & Go Live*, che mostra la stessa procedura su
Apex via Rithmic), help center Lucid (piattaforme e regole, verificati il 23/10/2026), forum e
supporto MultiCharts sulle licenze.

## 1. All'acquisto della eval: **scegliere Rithmic**

Lucid divide le piattaforme per connessione
([fonte](https://support.lucidtrading.com/en/articles/11404614-lucid-trading-supported-platforms)):

| connessione | piattaforme |
|---|---|
| CQG | NinjaTrader, Tradovate, TradingView |
| **Rithmic** | Quantower, Tradesea, MotiveWave, Sierra Chart, Jigsaw, Bookmap, ATAS, R\|Trader Pro, **MultiCharts** |

> **Se l'account nasce su CQG, MultiCharts non si collega.** E' la scelta da non sbagliare.

Strategie automatiche **permesse** su LucidFlex, news **permesse**, flat obbligatorio a fine
giornata (DriftPullback chiude alle 14:55: ok).

## 2. R|Trader Pro, una volta sola

Gratuito, e' la piattaforma ufficiale Rithmic. Serve solo ad abilitare i plugin:

1. login con le credenziali Lucid; **System** e **Gateway** come da email di benvenuto Lucid
   (sul corso, per Apex: System «Apex», Gateway «Chicago Area»);
2. controllare che *orders* e *market data* siano accesi;
3. **File → Allow Plugins.** *«if the plugins are not allowed, MultiCharts cannot establish the
   connection»* (Lesson 10, 30:40);
4. poi si puo' chiudere.

## 3. MultiCharts: Rithmic come sorgente dati

Quote Manager → Tools → Data Sources → **Rithmic** → Settings: login, password, System,
Gateway **Chicago Area**, e **tre spunte tolte**: *Aggregated Quotes*, *Connect via Rithmic
Trader Pro*, *Show Data Connection Alert*. Attivare la sorgente.

## 4. MultiCharts: Rithmic come broker

File → Broker Profiles → Manage → **New** → Rithmic. Stessi campi, *Lookup* per vedere gli
exchange, **Connect**. Deve comparire l'account con **saldo 50.000**. Sul VPS il profilo si
chiama «Rithmic».

## 5. Il grafico: dati Rithmic, contratto di dicembre

TradeStation serve solo per i test: il live prende i dati da Rithmic (Lesson 10, 33:02:
*«You can use as data source now Rithmic as well»*). Un punto di rottura in meno.

- **NQZ6 5 min** con **data2 NQZ6 15 min** (Insert → Series, stesso simbolo), sorgente
  **Rithmic**, Globex 24h, timezone **Exchange (CT)**;
- **NQ, non MNQ**: il VWAP di sessione e' pesato sui volumi, e il backtest usa quelli di NQ;
- **non l'`@NQ` di Rithmic**: e' un *Custom Futures* costruito da MultiCharts
  (`!NQ_101C0^HMUZ`), con regole di rollover non verificate contro il backtest. NQZ6 ha i prezzi
  del contratto attivo, che fino al rollover coincidono con l'`@NQ` TradeStation del backtest
  (non back-adjusted, verificato il 29/09);
- **storico**: la MA a 20 barre da 15 minuti chiede 5 ore, il VWAP parte alle 8:30 CT. Le barre
  dalla notte bastano; meglio averne qualche giorno;
- segnale **`Drift_LIVE`** = il codice di **`DriftPullback_v21.txt`** (il vecchio
  `DriftPullback.txt` non si usa). Input uguali al backtest: `DriftMode 0`,
  `DriftThreshPct 0.10`, `MALen 20`, `DriftLen 4`, `PullbackWindow 6`, `ExitMode 0`, SL/TP
  80/40/80/50, `StopSlipTicks 2`, `MaxTradesPerDay 4`, `MaxLossesPerDay 2`, `ShowLog 0`,
  `SizeMode 1`, **`BaseCts 2`** (il default e' 1) — il piano veloce dello Stage 7.

## 6. Symbol mapping: **NQZ6 → MNQZ6**

File → Broker Profiles → **Symbol Mapping** → il profilo Rithmic → **Add** → **NQZ6**
(sorgente Rithmic) → tre puntini «…» → **MNQZ6** (Micro, CME; se il lookup non lo trova,
`MNQZ26`) → OK → Apply. Il segnale si calcola su NQ, l'ordine va sul micro (Lesson 10, 06:40):
i punti sono gli stessi, stop e target non cambiano.

> ⚠️ **Al broker mai NQZ6.** 2 NQ valgono $40 al punto: lo stop da 80 punti e' una perdita di
> $3.200, oltre l'MLL.

Il grafico conta i 2 contratti come NQ: **il P&L sul grafico e' 10 volte quello del conto**.
Fa fede la dashboard Lucid.

> **Rollover, intorno all'11 dicembre**: si cambiano **due cose**, a mercato chiuso: il grafico
> (data1 e data2) in **NQH7** e il mapping in **NQH7 → MNQH7**. Poi si riattiva la strategia.
> Se ce ne si dimentica, la strategia smette di eseguire.

## 7. Le impostazioni di Auto Trading (proprieta' della strategia)

Ci si arriva dalla **freccina** accanto al pulsante SA/AA sul grafico → **Strategy Properties**
→ scheda **Auto Trading** (oppure tasto destro → Format Signals → Properties).

| | valore | perche' |
|---|---|---|
| real-time data | **dal grafico** | il caso comune, e lo stesso dato che genera il segnale |
| modo | **asincrono (AA)** | il corso lo consiglia: la posizione la gestisce la strategia |
| ordini stop / limit | Price Orders Emulation: **Stop Orders = Emulate locally using Bid/Ask and send a Market order**; Stop Limit e Limit = *Use native* (il TP resta al broker). Serve il prezzo in tempo reale di MNQZ6 da Rithmic (come dice il corso, Lesson 10, 35:28) | con *Native* il 27/10 ogni `L.SL` e' partito come **ordine a mercato** alla barra dopo l'entrata: 4 trade su 4 chiusi dopo 5 minuti (vedi diario). Con l'emulazione lo stop vive solo su MultiCharts: se il VPS si blocca non c'e' stop al broker |
| *Require order confirmation* | **tolta** | altrimenti ogni ordine aspetta un clic |
| *Assign initial market position* | **mostra sempre la finestra** | la rete di sicurezza: si conferma che grafico e broker sono flat |
| broker plugin | **Rithmic** + l'account (ingranaggio, *Lookup*) | va riselezionato ogni volta che si imposta la strategia |

**L'ingranaggio accanto al broker plugin** apre le proprieta' della connessione (System
LucidTrading, Gateway Chicago Area). In fondo, *Default Order Settings*: **Exchange CME** e
**Account LFE050-…** (con *Lookup*). Il 26/10 l'account era vuoto e Rithmic ha rifiutato tutti
gli ordini: *«Invalid order parameters: Account field is empty»*.

**Prima di accendere AA, ogni volta, tre controlli:**

| | dove |
|---|---|
| account compilato, exchange CME | Strategy Properties → Auto Trading → ingranaggio |
| **data2 a 15 minuti** | il pannello sotto il grafico |
| `BaseCts 2`, `SizeMode 1` | Format Signals → Inputs |

Poi **Automate Order Execution**: chiede conferma, si verifica *flat* su entrambi i lati,
*Apply*, il pulsante diventa **verde** con **AA**.

**Durante la sessione le credenziali Lucid non si usano altrove** (R\|Trader Pro, altre
piattaforme, un altro MultiCharts): Rithmic ammette un login per credenziale e butta fuori
l'altro. Il conto si guarda dalla dashboard Lucid nel browser, che non passa da Rithmic.

Dopo il primo segnale: scheda **Orders** dell'Order and Position Tracker, con **Account
compilato** e stato **Filled**. Se e' *Rejected*, la ragione e' nella scheda **Logs**.

Per cambiare queste impostazioni: **solo a strategia flat**. Si spegne l'automazione, si
modifica, si riaccende. Alla riaccensione MultiCharts ricalcola lo storico e puo' disegnare
trade che il conto non ha fatto: si controlla nell'**Order and Position Tracker** (View) e sulla
dashboard Lucid.

## 8. Dove gira: **VPS**, e la licenza

*«if you lose internet connection or your computer shuts down, MultiCharts will deactivate the
auto execution of your orders. What I highly suggest to you is to set up a VPS»* (Lesson 10,
22:41). MultiCharts gira solo su Windows; su un Mac (anche in macchina virtuale) basta un
aggiornamento o uno sleep per spegnerla.

**Una licenza MultiCharts = un computer alla volta**
([supporto MC](https://www.multicharts.com/support/base/do-i-need-an-additional-license-to-run-multicharts-on-another-computer/)).
Si puo' installare su Mac e VPS, ma il login sul secondo fa logout dal primo; usarli insieme
richiede una seconda licenza, e MultiCharts si riserva di revocarla se la regola non e'
rispettata.

**E non si vuole comunque**: due istanze che automatizzano lo stesso account mandano **ordini
doppi**. MultiCharts sul VPS e basta; dal Mac si controlla dalla dashboard Lucid.

**Test sul VPS, fuori orario.** Un workspace **LIVE** (solo il grafico di `Drift_LIVE`) e uno
**TEST** con i dati TradeStation. Gli studi sono condivisi fra i workspace: ricompilare un
segnale ricalcola **ogni** grafico che lo usa, quindi `Drift_LIVE` non si tocca e i test usano
copie con un altro nome. Niente lavoro pesante fra le **14:30 e le 22:00** italiane (dal 2/11:
13:30-22:00, quando gli USA tornano all'ora solare). Windows Update in manuale.

**Requisiti del VPS** (verificati il 25/10/2026):

| | |
|---|---|
| sistema | Windows Server 2022 o 2025 (MultiCharts gira solo su Windows, vuole .NET 4.8) |
| RAM | **almeno 8 GB**: e' il minimo ufficiale di MultiCharts 64 ([tech specs](https://multicharts.com/tech-specs/)). I piani da 4 GB non bastano |
| dove | **Chicago**, vicino ai server Rithmic e al CME |
| Lucid | nessun divieto: i sistemi automatici sono permessi (*Other Trading Activities*), VPS e IP non sono citati |

Scelta: **AlgoVPS Swing**, $45/mese, 4 core Ryzen 9950X, **10 GB**, 100 GB NVMe, Windows
Server 2022/2025, datacenter di Chicago (427 S La Salle, consigliato per CME), disdetta quando
si vuole ([prezzi](https://algovps.com/pricing)). Alternativa: QuantVPS Lite+ a $79,99 con
8 GB e 14 giorni di rimborso. Lo Starter+ di QuantVPS da $39,99 ha 4 GB: sotto il minimo.

## 9. Due date da non perdere

| data | cosa |
|---|---|
| **27/11** | Black Friday: decisione sulla licenza MultiCharts |
| **29/11** | **fine del mese gratuito**. Se scade a eval aperta, **l'automazione si ferma** |
| **~11/12** | rollover: grafico NQZ6 → NQH7 **e** mapping → NQH7 → MNQH7 |

Il piano veloce ha una mediana di **22 giorni**: partendo il 26/10 si chiude probabilmente
prima del 29/11, ma la finestra di 60 giorni arriva a gennaio.

## 10. La prima settimana vale da Stage 9

Il pipeline chiede *paper almeno una settimana*. La eval **e'** capitale simulato: la prima
settimana fa da verifica, a patto di **confrontare ogni trade reale col backtest dello stesso
giorno** — stessi ingressi, stessi orari, stesse uscite. Se divergono, ci si ferma e si capisce
perche' prima di continuare.

E le soglie dello Stage 9 restano: drawdown al **75esimo percentile → si riduce**, al **95esimo
→ si ferma**.

## 11. Diario del live

| data | cosa |
|---|---|
| 26/10/2026 | **Live.** R\|Trader Pro: due errori al login (*Permission to connect to the Infrastructure*, *License server could not be contacted*), risolti da Mario. Partito in SA, passato ad AA verso le 9:45 CT. Il long delle 9:45 chiuso a target sul grafico era **solo il ricalcolo** del passaggio SA → AA: conto flat |
| 26/10/2026, sera | **Nessun trade sul conto.** Il grafico ha generato tre long (10:10, 10:30, 12:25 CT, che a 1 contratto davano +40, −80,5, −80,5 punti), tutti **rifiutati**: *«Account field is empty»*. Due logout forzati alle 9:47 CT (le stesse credenziali usate altrove), ricollegato da solo |
| 27/10/2026 | Trovata anche **data2 a 5 minuti** invece di 15. Corretti prima dell'apertura: data2 a 15 minuti, account LFE050-… ed exchange CME nelle proprieta' della connessione. Aggiunti i tre controlli prima di accendere AA (sezione 7) |
| 27/10/2026, sera | **Primi trade sul conto.** 4 entrate su 4 eseguite nella stessa barra del grafico, slippage 0,25–0,5 punti. **Uscite diverse dal grafico:** il grafico dice TP, TP, SL alle 13:05, TP alle 14:40 (+$158 in MNQ); il conto chiude il terzo e il quarto trade entro 5 minuti dall'entrata (Realized P/L dell'ultima riga −$7). Il terzo ingresso eseguito in due pezzi (1+1). Da diagnosticare con Orders e Logs |
| 28/10/2026 | **Diagnosi del 27/10.** Orders: in tutti e 4 i trade `L.SL` e' partito **a mercato** all'apertura della barra dopo l'entrata (10:15, 10:40, 11:15, 14:20 CT), il `L.TP` limit e' stato cancellato senza arrivare al broker. Conto: +31, +21,25, −16,25, −1,75 punti = **+$137** lordi; il grafico, che li tiene fino a TP/SL, fa +$158. Causa probabile: con ordini *Native* MultiCharts considera lo stop gia' toccato e lo converte in market (forse perche' non ha il prezzo di MNQZ6, che non e' sul grafico). Rimedio: **Emulate locally**, da verificare al primo trade. La dashboard Lucid non mostra ancora i trade (*No Trading Data*) |
