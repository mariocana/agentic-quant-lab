# Protocollo di test — versione MultiCharts (Fase 2)

Sostituisce `mql5/docs/fase2_testing.md` per le strategie portate su MultiCharts.
Fonte: Institutional Protocol (vedi `institutional_protocol_digest.md`) + le nostre
regole già in uso (lotti fissi, split‑sample per i filtri, niente compounding).

Regola zero: **una strategia = una ipotesi in una frase + una ragione per cui dovrebbe
funzionare.** Se non riesci a scriverla, non si parte.

---

## 0. Setup una tantum
- [ ] Workspace `Institutional Protocol` salvato; Strategy Properties → Max bars back ≥ 300.
- [ ] Session template controllato: chart in **Exchange time (CT)**; RTH = 08:30–15:00 CT;
      Globex 17:00–16:00 CT. Tutti gli input orari nel codice sono in **ora del chart**.
- [ ] Costi di default salvati come regola: NQ **$2.50/lato + 1 tick** slippage
      (GC: $2.50 + 1 tick; CFD: spread reale). Mai testare a costo zero.
- [ ] Coerenza provider: stessa strategia, stessi 100 giorni su due feed → stesso n. trade
      e P&L (± pochi %). Solo dopo scarichi 5–10 anni.
- [ ] Simbolo di sviluppo = contratto più liquido (**NQ**, GC), continuous (@NQ).
      Il micro si usa solo per il live (symbol mapping).

## 1. Sviluppo (iterativo, un pezzo alla volta)
1. Versione 1 = solo entrata + uscita a tempo, 1 contratto. Compila, applica su
   ~100 giorni, **verifica a occhio** e nella lista trade che entri/esci dove previsto
   (orari, next‑bar, weekend).
2. Aggiungi un elemento per volta (filtro, TP, SL, short leg) → nuovo signal `_v2`,
   `_v3`… (i checkpoint restano compilati). Ricontrolla lista trade: TP/SL ≈ punti × $/pt.
3. Input separati long/short (TP/SL) per poterli ottimizzare a parte.
4. Indicatori di supporto sul chart (ORB box, Donchian, VWAP…) solo per la verifica visiva.
5. Numero contratti come input; SL/TP **in punti** (scalano da soli). Se in $, ricorda
   che `SetStopLoss` è per posizione.

## 2. Backtest base (1 contratto, costi on)
- Periodo: tutto lo storico disponibile, ma **IS = 80%, OOS = 20% finale**, date scritte
  prima. L'OOS **non si tocca** fino al punto 5.
- Metriche da annotare (Strategy Performance Report):
  net profit, % profitable, **avg trade**, max strategy DD ($), max value DD, PF,
  n. trade, long vs short, equity curve.
- **Gate 1** (IS): avg trade ≥ soglia strumento (NQ $70 → MNQ $10; GC $140 → MGC $20;
  target "sano" ~$100 su NQ); PF ≥ 1.2; DD $/contratto compatibile col conto (micro ÷10);
  n. trade ≥ 200; equity senza "un solo anno che fa tutto"; tabella annuale con segno
  stabile (2021–23 vs 2024+).
- Base case: la versione **senza filtri** è il benchmark. Trend Following Regime Check
  sullo strumento prima di scegliere la famiglia.

## 3. Monte Carlo built‑in (IS)
- Reshuffle: 1000 sim, 100% trade. Guardo: DD peggiore (è il DD da budgettare),
  mediana net profit > 0, % sim in perdita < 10%, dispersione.
- Distribution analysis: percentili di DD e net profit.
- **Gate 2**: mediana > 0, < 10% sim negative, DD 95° perc. sostenibile con la size prevista.

## 4. Miglioramento e ottimizzazione (solo IS)
- Ogni filtro nuovo: deve avere una ragione + **split‑sample** (due metà dell'IS, deve
  migliorare l'avg trade in entrambe). Altrimenti è rumore → scartato.
- Ottimizzazione a due passi, max 2–3 input alla volta, step larghi; scegli il
  **cluster**, non il picco. Fitness: PF o avg trade, non net profit.
- Domande di controllo: regole semplici e coerenti? ho evitato l'ottimizzazione
  capillare? Se una risposta è no, torna indietro.

## 5. Out‑of‑sample (una volta sola)
- Applica i parametri congelati all'OOS. **Gate 3**: avg trade, % profitable, PF nello
  stesso ordine di grandezza dell'IS; DD non esplode; equity con drift positivo.
- Se l'OOS fallisce: la strategia va nel "cimitero", **non si ri‑ottimizza sull'OOS**.

## 6. Bootstrap (Colab del corso, IS + OOS)
- Esporta "List of trades" (Save → solo lista trade) e carica nel notebook Monte Carlo
  (link in `4. Validation…/2. Colab_Montecarlo.txt`; risk per contract = SL in $).
- **Gate 4**: EV > 0 in $ e in R; P(EV ≤ 0) < 5% IS e < 10% OOS; CI IS/OOS sovrapposti;
  drift positivo negli spaghetti.
- Salva i percentili di DD dopo 10/20/40/100 trade: sono i yardstick del live
  (75° → dimezza rischio, 95° → stop).

## 7. Walk‑forward (facoltativo, quando serve)
Usalo se: pochi anni di dati, asset regime‑dipendente, o se vuoi una regola di
ri‑ottimizzazione periodica. Setup: IS 252 / OOS 63 sessioni, rolling, fitness PF,
esaustivo su ≤ 30 combinazioni; criteri **prima** del run: avg OOS profit > 0,
avg OOS PF > 1.1, ≥ 60% finestre profittevoli, nessuna finestra > 50% del profitto,
≥ 30 trade/finestra, WFE ≥ 60%. Fail su uno = fail.

## 8. Sizing
- Capitale proprio: contratti = max DD tollerato ÷ DD 95° perc. (bootstrap). Se < 1 →
  micro. Confronta sempre **fixed** vs **rischio $ costante** (vol targeting, non composto)
  sul return/DD, come già facevamo su MT5.
- Prop: **Colab prop simulator** (single/multiple) → size ottimale per l'eval, size
  di sopravvivenza per il funded, pass rate a 1/2/3/4 tentativi, correlazione fra
  strategie (target ~0 o negativa). Regole Apex 50k nel digest.
- Il basket va simulato **insieme**, non strategia per strategia.

## 9. Go‑live
- Paper trading ≥ 1 settimana (ordini, orari, fill). Poi micro per i primi giorni.
- Auto trading: Async, dati dal chart, conferma off, symbol mapping sul front month
  (aggiorna 2 gg prima della scadenza), VPS se > 1 strategia.
- Monitoraggio: avg trade live vs backtest (3 mesi), DD live vs percentili.
  Cambi solo nel sandbox, mai sul live. L'unica cosa che si tocca live è il n. contratti.

---

## Piano immediato
1. **ORB NQ 5m** (= Fabio Model): porting di `OrbBreakout_EA` in PowerLanguage,
   parametri come validati (range 08:30–09:00 CT, TP 1R, flat 14:00 CT, long only),
   con e senza filtro delta. Passi 2→6. Confronto con i numeri del report (avg $183, WR
   58%, PF 1.28) come sanity check del setup.
2. Regime check + `NQ_Session_Tester` su NQ e GC.
3. VWAP‑ADX (mean reverting) e Gold Asian Range (altro asset) → basket a 3.
4. `PropGuard` in PowerLanguage (daily loss, DD statico, target, flat weekend, scaling).
