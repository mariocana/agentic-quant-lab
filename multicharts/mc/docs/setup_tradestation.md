# Setup TradeStation → MultiCharts (giorno del funding)

Da fare nell'ordine, appena i fondi sono accreditati sul conto **Futures**.

## 1. TradeStation
- [ ] Verifica che il conto Futures risulti **funded** e che nel Client HUB compaiano le
      entitlement dati CME/CBOT/NYMEX/COMEX (profilo **NON‑PRO**). Da qui partono i 90 giorni gratis.
- [ ] Installa e apri la **TradeStation Desktop app**, fai login: deve restare aperta in
      background perché MC la usi come feed.

## 2. MultiCharts
- [ ] Attiva il piano **Standard**. Crossgrade ottenuto dal supporto (29/09/2026): **primo
      mese gratis + secondo a $90** → copertura fino al **29/11**, con il Black Friday
      (27/11) dentro la finestra. La lifetime va comprata entro il **29/11**: dopo si resta
      senza piattaforma.
- [ ] Wizard: ☰ → Help → Run Wizard → "ho già data source, login e password" →
      **TradeStation** → account **live** → Test → login → Next. Broker: per ora paper.
- [ ] File → Broker Profiles → Manage: TradeStation deve risultare **Connected**.

## 3. Verifica profondità storico (il dato che serve alla pipeline)
- [ ] New chart → data source TradeStation → **@NQ**, resolution **5 min**,
      range dal **2016‑01‑01** a oggi → OK, e aspetta il backfill completo.
- [ ] Annota la **data della prima barra** effettivamente caricata. Ripeti con
      **@NQ 1 min** (per VWAP Pullback) e **@GC 15 min** (Gold Asian).
- [ ] QuoteManager → il simbolo mostra il range scaricato: lo storico resta **in locale**
      anche dopo la scadenza dei dati real‑time.

## 3b. Scaricare lo storico (una volta sola)
Regola: **barre da 1 minuto, non tick**. Da 1 min MC comprime 5 e 15 min, quindi un solo
download per strumento copre tutte le strategie; lo storico a tick è più corto, pesa
centinaia di milioni di righe e rende lente ottimizzazioni e backtest.
- [ ] @NQ **1 min**, range dal 2016 (o dalla prima barra disponibile) a oggi. Un solo
      download copre **cinque** strategie: ORB, VaultBreak e NQ First5 (compressione a
      5 min), DriftPullback (5 **e** 15 min), VWAP Pullback (1 min nativo).
- [ ] @GC **1 min**, stesso range → Gold Asian per compressione a 15 min.
- [ ] Lascia completare il backfill; i dati restano nel database locale anche quando
      scadono i 90 giorni di real‑time.
- [ ] **Bar Magnifier** (Strategy Properties): attivo, risoluzione 1 minuto. Serve per i
      fill intrabar sulle barre da 5 min, dove stop e target possono essere toccati nella
      stessa barra. Nei report fatti con i dati di prova era *Disabled*.
- [ ] Tick: **non ora**. Se serviranno (filtro delta, precisione fill), se ne scarica una
      finestra di 1–2 anni, non tutto lo storico.
- Nota piano: l'Historical Data Downloader con scheduler è una funzione **Advanced**; con
  Standard il backfill si fa aprendo il chart con il range pieno.

## 4. Impostazioni comuni prima dei test
- [ ] Format Instrument → Settings → Time zone **Exchange** (CT). Verifica che l'apertura
      cash cada alle **08:30**.
- [ ] Session template: RTH 08:30–15:00 CT per VaultBreak; Globex 24h per ORB, VWAP, GC,
      NQ First5 e DriftPullback.
- [ ] **DriftPullback** vuole due serie sullo stesso chart: @NQ 5 min come Data1, poi
      Insert → Instrument → stesso simbolo a **15 min** come Data2. L'ordine conta.
- [ ] Strategy Properties → Properties → commissione **$2.50/contratto per lato**,
      slippage **1 tick**; salvale come regola riutilizzabile.
- [ ] Max bars back: 100 (ORB, VaultBreak, GC, NQ First5, DriftPullback), **≥ 300** per
      VWAP Pullback su 1 min.
- [ ] Salva workspace e desktop.

## 5. Coerenza dei dati (prima di fidarsi dei 5 anni)
- [ ] Rigira l'ORB sugli **stessi 100 giorni** già testati con dxFeed sample: n. trade e
      P&L devono coincidere a meno di pochi punti percentuali. Se divergono molto,
      controlla session template e timezone prima di proseguire.

## Ordine di lavoro dopo il setup

1. **ORB** → è l'unica già a Gate 1 passato: va direttamente allo **Stage 2**
   (IS 2020‑01‑01 → 2024‑12‑31, 1 contratto, costi on).
2. Le altre cinque devono prima passare lo **Stage 1** (meccanica, ~100 giorni, `ShowLog`):
   VaultBreak (chart RTH, `DailyATRLen 20` per il lead‑in) → NQ First5 → DriftPullback
   (due serie) → VWAP Pullback → Gold Asian.
3. Subito dopo lo Stage 2 di ORB e First5: **misurare la correlazione** fra le due, senza
   aspettare il gate 8. Stesso strumento, stessa ora, stessa idea di drift.

Configurazioni da usare allo Stage 1 e 2: quelle **validate**, cioè tutti i default.
`EntryMode`, `TriggerMode`, `UseFilters`, `StopPts`, `SizingMode` restano a 0 — sono
varianti dello Stage 4, non si accendono prima.
