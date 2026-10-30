# ESCounter — istruzioni Stage 1

Codice: `ESCounter.txt` (signal). Spec: `SPEC.md`.

## Chart
- **data1: @ES · 30 min**, **data2: @ES · 1440 min** (Insert Instrument, stesso simbolo,
  stessa sessione). Data source TradeStation, timezone **Exchange** (CT).
- **Session template Globex 17:00–16:00 CT, senza pause**, su entrambe le serie. Non il
  template vecchio con la pausa 15:15–15:30 (è quello che tagliava l'export di @ES).
- Bar Magnifier **1 min ON**, Backtesting Mode Classic, Max bars back 50.
- Costi: **`15$ per Contract`**, slippage **`0 ticks`**. Point Value @ES = $50.
- Periodo per lo Stage 1: gli **ultimi ~100 giorni** di borsa.

## Run dello Stage 1

| run | `FlatEOD` | `MaxEntries` | `Num` | file in `reports/` |
|---|---|---|---|---|
| A | 0 | 0 | 1 | `ESC_S1_A_orig_x1.xlsx` |
| A10 | 0 | 0 | 10 | `ESC_S1_A_orig_x10.xlsx` |
| B | 1 | 2 | 1 | `ESC_S1_B_prop_x1.xlsx` + log (`ShowLog 1`) |

Per il run A10 la size si imposta in Strategy Properties → Default Trade Size = 10 (il
codice non ha un input per i contratti, come l'originale). Gli altri input ai default:
`Myloss 700`, `myProfit 1500`, `mybars 1`, `starttime 1730`, `endtime 1530`.

## Verifica meccanica (Gate 1)

1. **MyLow giusto**: ogni riga `ESC LOW` del log è alle **17:30** e `mylow` è il minimo della
   sessione appena chiusa (17:00 → 16:00). Controllane due a mano sul chart. Se `mylow`
   corrisponde al minimo della sola sessione cash, data2 ha un template diverso da data1.
2. **Ingresso giusto**: ogni `ESC SIG` ha la barra precedente con close ≤ `mylow` e quella
   del segnale con close > `mylow`. L'entrata è sulla barra successiva, al suo open.
3. **Finestra**: nessuna entrata fra 15:30 e 17:30.
4. **Stop e target**: le uscite si chiamano `Stop Loss` e `Profit Target` e sono a
   **−14 / +30 punti** dall'entrata (P&L lordo −$700 / +$1.500 per contratto, prima dei costi).
   Contare quante uscite **non** sono né stop né target: nel run A dovrebbero essere zero
   (salvo il trade aperto a fine periodo). È la verifica del rapporto 1,04 di Unger (spec).
5. **Variante B**: tutte le posizioni sono flat alle **16:00** (uscita `ExitOnClose` o simile
   sull'ultima barra della sessione); **al massimo 2 ingressi per sessione** (`ingressi_sessione`
   nel log non supera 1 al momento del secondo segnale).
6. **Variante A**: annota quanti trade restano aperti oltre la sessione e oltre il weekend, e
   il peggior trade: è la misura del rischio di gap che la spec usa per giustificare la B.
7. **Scala ×10**: il P&L di A10 è esattamente 10 volte quello di A.
8. **Tetto ingressi**: conta i giorni con 2 ingressi in B e i giorni con più di 2 in A.

## Cosa mi mandi
I tre `.xlsx` e il log del run B.
