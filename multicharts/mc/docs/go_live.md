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
exchange, rinominarlo «Lucid», **Connect**. Deve comparire l'account con **saldo 50.000**.

## 5. Il grafico: identico al backtest

- **@NQ 5 min** con **data2 a 15 min**, Globex 24h, timezone **Exchange (CT)**;
- **la stessa serie del backtest** (non back-adjusted: `driftPct` usa una percentuale del
  prezzo, e lo abbiamo verificato il 29/09);
- **storico caricato a sufficienza** perche' MA a 20 barre da 15 minuti e VWAP di sessione siano
  gia' caldi all'apertura: almeno qualche giorno;
- input **uguali al backtest** (`DriftMode 0`, `DriftThreshPct 0.10`, `MALen 20`, `DriftLen 4`,
  `PullbackWindow 6`, SL/TP 80/40/80/50, `StopSlipTicks 2`, `MaxTradesPerDay 4`,
  `MaxLossesPerDay 2`, `SizeMode 1`), con **2 contratti** — il piano veloce dello Stage 7.

## 6. Symbol mapping: @NQ sul grafico, **MNQZ6** al broker

File → Broker Profile → **Symbol Mapping** → il profilo Lucid → Add: **@NQ → MNQZ6** (dicembre
2026). Il segnale si calcola sulla serie continua, l'ordine va sul micro (Lesson 10, 06:40). I
punti sono gli stessi, quindi stop e target non cambiano.

> **Rollover**: MNQZ6 scade a meta' dicembre. **Intorno all'11 dicembre** il mapping va
> spostato su **MNQH7**. Se ce ne si dimentica, la strategia smette di eseguire.

## 7. Le impostazioni di Auto Trading (proprieta' della strategia)

| | valore | perche' |
|---|---|---|
| real-time data | **dal grafico** | il caso comune, e lo stesso dato che genera il segnale |
| modo | **asincrono (AA)** | il corso lo consiglia: la posizione la gestisce la strategia |
| *Require order confirmation* | **tolta** | altrimenti ogni ordine aspetta un clic |
| *Assign initial market position* | **mostra sempre la finestra** | la rete di sicurezza: si conferma che grafico e broker sono flat |
| broker plugin | **Rithmic / Lucid** + l'account | va riselezionato ogni volta che si imposta la strategia |

Poi **Automate Order Execution**: chiede conferma, si verifica *flat* su entrambi i lati,
*Apply*, il pulsante diventa **verde**.

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

**Requisiti del VPS** (verificati il 25/10/2026):

| | |
|---|---|
| sistema | Windows Server 2022 o 2025 (MultiCharts gira solo su Windows, vuole .NET 4.8) |
| RAM | **almeno 8 GB**: e' il minimo ufficiale di MultiCharts 64 ([tech specs](https://multicharts.com/tech-specs/)). I piani da 4 GB non bastano |
| dove | **Chicago**, vicino ai server Rithmic e al CME |
| Lucid | nessun divieto: i sistemi automatici sono permessi (*Other Trading Activities*), VPS e IP non sono citati |

Scelta: **QuantVPS Lite+**, $79,99/mese, 4 core, 8 GB, Chicago, Windows Server 2025, senza
vincoli e con 14 giorni di rimborso. Lo Starter+ da $39,99 ha 4 GB: sotto il minimo.

## 9. Due date da non perdere

| data | cosa |
|---|---|
| **27/11** | Black Friday: decisione sulla licenza MultiCharts |
| **29/11** | **fine del mese gratuito**. Se scade a eval aperta, **l'automazione si ferma** |
| **~11/12** | rollover MNQZ6 → MNQH7 |

Il piano veloce ha una mediana di **22 giorni**: partendo il 26/10 si chiude probabilmente
prima del 29/11, ma la finestra di 60 giorni arriva a gennaio.

## 10. La prima settimana vale da Stage 9

Il pipeline chiede *paper almeno una settimana*. La eval **e'** capitale simulato: la prima
settimana fa da verifica, a patto di **confrontare ogni trade reale col backtest dello stesso
giorno** — stessi ingressi, stessi orari, stesse uscite. Se divergono, ci si ferma e si capisce
perche' prima di continuare.

E le soglie dello Stage 9 restano: drawdown al **75esimo percentile → si riduce**, al **95esimo
→ si ferma**.
