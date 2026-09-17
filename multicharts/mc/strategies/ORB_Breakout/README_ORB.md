# ORB_Breakout — istruzioni per il primo test in MultiCharts

Codice: `ORB_Breakout.txt` (signal PowerLanguage). Indicatore di supporto: l'**ORB Box**
del corso (`mc/protocollo/6. Code Templates/2. Indicators/4. OpeningRangeBreakout_Box.txt`),
serve solo per vedere il range sul chart.

## 1. Compila
1. Study Editor → New → **Signal** → nome `ORB_Breakout` → incolla il file → **Compile** (F3).
2. Stessa cosa per l'indicatore ORB Box (New → **Indicator**), input `ORStartTime 830`,
   `ORLengthMinutes 30`, `SessionEndTime 1500` (ora del chart, vedi sotto).

## 2. Chart
- New chart → data source **dxFeed sample** (o Simulated) → **NQ** (o ES/MNQ se NQ manca).
- Resolution **5 min**, range: gli ultimi **100 giorni** (prima di tutto va verificata la
  meccanica, non la statistica).
- Format Instrument → Settings → **Time zone: Exchange** e session template CME / RTH.
  Guarda l'asse dei tempi: l'apertura cash deve cadere alle **08:30** (Chicago). Se cade
  alle 09:30 il chart è in ET → metti `ORB_Start_H 9`, `Trade_End_H 15`.
- Format → Strategy Properties → Properties → **Max bars back 100**.
- Strategy Properties → Properties → commissioni `$2.50` per contratto per lato e
  slippage 1 tick (NQ 0.25 = $5). Salvale come regola.

## 3. Applica e verifica a occhio (obbligatorio)
Insert Study → Signals → `ORB_Breakout`, input di default (long only, 1 contratto, 1R).
Poi controlla sul chart e in **Strategy Performance Report → List of Trades**:
- l'ingresso avviene sulla **chiusura della prima barra** che chiude sopra il box, dopo
  le 09:00 e prima delle 14:00;
- lo stop è al **low del box**, il target a **+1R**; con `ShowLog true` i livelli sono
  stampati nel PowerLanguage Output;
- **un solo trade al giorno**; nessuna posizione oltre le 14:00; nessun trade che salta
  il weekend;
- con 10 contratti il P&L per trade deve essere ×10 (sanity dello scaling).

Se qualcosa non torna, manda uno screenshot del chart + la lista trade.

## 4. Poi (quando la meccanica è giusta)
- Storico lungo: i dati free bastano per la meccanica, non per la statistica. Per i
  5 anni servono TradeStation (deposito $500 → dati gratis 6 mesi) o IQFeed.
- Con lo storico: protocollo `mc/docs/protocollo_test_mc.md` passi 2→6.
  Numeri di riferimento del corso (NQ 5m, 2021‑26, 1 contratto, costi on):
  avg trade **$183**, WR **58%**, PF **1.28**, max DD **$25.9k**, ~160 trade/anno.
- Esperimenti nell'ordine: `AllowShort true` (atteso: aggiunge poco), `UseDeltaFilter
  true` (solo se il feed ha UpTicks/DownTicks ≠ 0), `SizingMode 1` vs 0 sul return/DD,
  `ORB_Dur_Min 60` (variante IB).

## Note sul codice
- Barre timbrate a fine periodo: il range usa le barre con `Time` in
  `(ORB_Start, ORB_End]`, cioè 08:35…09:00 = i primi 30 minuti.
- Ingresso `this bar on close`; bracket come ordini stop/limit **re‑emessi ogni barra**
  (fill intrabar realistici senza IOG). Il bracket è attivo già dalla prima barra
  dopo l'ingresso.
- Time exit `this bar on close` sulla prima barra che attraversa `Trade_End`.
- `SizingMode 1`: contratti = `Risk_USD / (R × BigPointValue)`, R in punti; non composto.
