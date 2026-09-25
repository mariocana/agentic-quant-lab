# Setup TradeStation → MultiCharts (giorno del funding)

Da fare nell'ordine, appena i fondi sono accreditati sul conto **Futures**.

## 1. TradeStation
- [ ] Verifica che il conto Futures risulti **funded** e che nel Client HUB compaiano le
      entitlement dati CME/CBOT/NYMEX/COMEX (profilo **NON‑PRO**). Da qui partono i 90 giorni gratis.
- [ ] Installa e apri la **TradeStation Desktop app**, fai login: deve restare aperta in
      background perché MC la usi come feed.

## 2. MultiCharts
- [ ] Acquista il piano **Standard** mensile (prima chiedi al supporto lo sconto crossgrade).
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

## 4. Impostazioni comuni prima dei test
- [ ] Format Instrument → Settings → Time zone **Exchange** (CT). Verifica che l'apertura
      cash cada alle **08:30**.
- [ ] Session template: RTH 08:30–15:00 CT per VaultBreak; Globex 24h per ORB, VWAP, GC.
- [ ] Strategy Properties → Properties → commissione **$2.50/contratto per lato**,
      slippage **1 tick**; salvale come regola riutilizzabile.
- [ ] Max bars back: 100 (ORB, VaultBreak, GC), **≥ 300** per VWAP Pullback su 1 min.
- [ ] Salva workspace e desktop.

## 5. Coerenza dei dati (prima di fidarsi dei 5 anni)
- [ ] Rigira l'ORB sugli **stessi 100 giorni** già testati con dxFeed sample: n. trade e
      P&L devono coincidere a meno di pochi punti percentuali. Se divergono molto,
      controlla session template e timezone prima di proseguire.

Poi si parte con lo **Stage 2** (`pipeline_prop.md`): backtest IS 2020‑01‑01 → 2024‑12‑31,
1 contratto, costi on, per ORB → VaultBreak → VWAP → GC.
