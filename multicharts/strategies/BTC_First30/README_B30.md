# BTC First30 Short — istruzioni Stage 1

Codice: `BTC_First30.txt` (signal). Spec: `SPEC.md`.

## Chart
- **@BTC · 5 min**, data source TradeStation, timezone **Exchange** (CT), Bar Magnifier
  **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- **Session template 24h, 17:00–16:00 CT, senza pause.** Non usare un template "RTH" o
  "US equity": la strategia ha bisogno della barra delle 15:00 per uscire e di quelle
  08:35–09:00 per misurare. Se il CME ha attivato il 24/7 sulle crypto, va bene anche un
  template 24/7: il codice esclude sabato e domenica.
- Costi: commissione **`175$ per Contract`** (50 MBT × $3,50/lato, slippage compreso),
  campo slippage **`0 ticks`**. Point Value @BTC = **$5**.
- Periodo del chart per lo Stage 1: gli **ultimi ~100 giorni** di borsa.
- Prima dello Stage 2, apri @BTC su gennaio 2020 e controlla che i prezzi siano positivi e
  plausibili. Se il continuo di TradeStation è back‑adjusted (lo è @ES), anni di roll
  mensili in contango possono spostare molto i livelli vecchi. Il codice lavora in punti,
  ma un prezzo ≤ 0 romperebbe il calcolo dello stop.

## Run dello Stage 1

| run | `StopMode` | `TradeShorts` / `TradeLongs` | `Num_Contracts` | file in `reports/` |
|---|---|---|---|---|
| A | 0 (originale) | 1 / 0 | 1 | `B30_S1_A_nostop_x1.xlsx` |
| B | 0 | 1 / 0 | 10 | `B30_S1_B_nostop_x10.xlsx` |
| C | 1 (estremo finestra) | 1 / 0 | 1 | `B30_S1_C_orstop_x1.xlsx` |
| D | 1 | 1 / 0, `TP_RR 1` | 1 | `B30_S1_D_orstop_tp1_x1.xlsx` |

Dopo il primo giro (17/10/2026) vanno **rifatti C e D** con il codice corretto; A e B
restano validi (senza stop il difetto non li tocca).

Tutti gli altri input ai default: `ORStart 830`, `OREnd 900`, `ExitTime 1500`,
`StopBufTicks 0`, `MaxRiskPts 4000`, `MinDropPts 0`. Su un run (C) metti `ShowLog 1` e
salva l'output del PowerLanguage Editor in `reports/B30_S1_C_log.txt`: serve per i
controlli 1, 4 e 6.

## Verifica meccanica (Gate 1)

1. **Finestra giusta**: nel log ogni riga `B30 OR` ha `t= 900`, `barre= 6`, `completa= 1`.
   `open` è il prezzo delle 08:30 e `close` quello delle 09:00: controllane due a mano sul
   chart.
2. **Entrata solo nei giorni negativi**: ogni trade del run A ha `delta` < 0 nel log del
   giorno. Nessun trade nei giorni con `delta` ≥ 0.
3. **Orari**: le entrate compaiono sulla barra **09:05** (prezzo = open delle 09:00), le
   uscite a tempo sulla barra **15:05** (prezzo = open delle 15:00). È il comportamento di
   `next bar at market`, come in GAR alle 10:15.
4. **Solo lunedì–venerdì**: nessun trade con `dow` 0 o 6. Se il chart ha barre nel weekend
   (CME 24/7), il log deve mostrare `short= 0` in quei giorni.
5. **Un trade al giorno, zero overnight**: nessun giorno con due trade, nessuna uscita
   `EXIT-S` in una data diversa dall'entrata.
6. **Stop (run C)**: lo stop di ogni trade = entry + `rischio_pt`, dove `rischio_pt` = `hi`
   della finestra − close delle 09:00 (log `B30 OR` e `B30 ENT`). Le uscite si chiamano
   **`Stop Loss`** e avvengono a quel prezzo o peggio. **Lo stop deve poter scattare già
   nella barra 09:00–09:05**: è il difetto del primo giro (vedi `CHECKLIST_Stage1.md`).
7. **Guardrail**: i giorni con `rischio_pt` > 4000 hanno `short= 0`. **Conta quanti
   sono** su ~100 giorni e riporta la distribuzione di `rischio_pt` (mediana, 90°
   percentile, massimo): è la misura che la spec chiede per lo Stage 1.
8. **Scala ×10**: il P&L del run B è 10 volte quello del run A.
9. **Target (run D)**: `TP=` nel log = entry − 1 × `rischio_pt`. Le uscite si chiamano
   **`Profit Target`** e avvengono **esattamente** a quel prezzo, mai meglio: un target
   riempito oltre il suo prezzo vuol dire che l'ordine non era attivo quando il prezzo ci
   è passato.
10. **Festività USA**: elenca i trade in giorni di festività USA o di orario ridotto CME.
    Non si tolgono adesso: si annotano.

## Cosa mi mandi
I quattro `.xlsx` e **il log del run C** (`ShowLog 1`, output del PowerLanguage Editor
salvato in un `.txt`): senza log i controlli 1, 2, 4 e 7 non si possono fare. Dal report leggo P&L, trade e uscite, e verifico i controlli
1–10. Con il Gate 1 chiuso si passa allo Stage 2 (IS 2020–2024, costi on).

## Nota sull'ipotesi
La tesi è asimmetrica: i ribassi del mattino proseguono, i rialzi no. Il lato long
(`TradeLongs 1`, `TradeShorts 0`) **non** è nello Stage 1, ma va misurato allo Stage 2
sullo stesso IS. Se rende quanto lo short, la ragione dichiarata è falsa (vedi spec, kill).
