# BIAS di Unger (bias orario su EURUSD) — **archivio, non testata**

Trascritta dai video del modulo 6 il 23/10/2026 e archiviata **senza run**: su LucidFlex 50k
è **causa B per costruzione**, e non si porta su altri strumenti.

## File
| file | cosa | fonte |
|---|---|---|
| `Mario_UngerBIAS.txt` | versione generica `DevelopBIAS`: `testphase 1` scansiona le barre della sessione, `testphase 0` è la strategia | video 6x01 (codice), `13. Codici/BIAS/setting1.png` (input) |
| `Mario_UngerBIAS_EURUSD.txt` | versione finale `DevelopBIASEURUSDFineTune`, quattro gambe a barre fisse | video 6x03 (codice al 6:40, parametri all'8:48) |

Entrambe chiamano **`Mario_PtnBaseSA`**. Nel video le righe d'ingresso della versione generica
escono dal bordo destro e sono state completate con `then buy / sellshort next bar at
market`, come le righe vicine. Nella versione finale i valori di `MyNotLEDay` e `MyNotSEDay`
dopo l'ultima ottimizzazione non si vedono nel video: restano a 0.

## La strategia
EURUSD forex **60 min**, dati TradeStation, grafico in ora di New York. Quattro gambe a
barre fisse della sessione (barra 1 = la prima dopo l'apertura):

| gamba | entrata → uscita | filtri |
|---|---|---|
| long | barra 19 → barra 1 del giorno dopo (posizione notturna) | ieri inside bar (38), non chiusura nel 20% basso (31), non martedì |
| short | 10 → 19 | pattern 2, non 9, non lunedì |
| long | 5 → 10 | pattern 36, non 23 |
| short | 1 → 5 | pattern 9 (3 chiusure in calo), non 4 |

Stop **0,016 = 160 pip**, nessun target.

## Perché è archiviata
- **Il conto.** Su Lucid l'EURUSD esiste solo come **6E intero** (125.000 €, $12,50 a pip):
  lo stop di 160 pip vale **$2.000 a contratto**, cioè l'**intero MLL** di LucidFlex 50k in
  un solo trade.
- **Il porting.** Le barre 19→1, 10→19, 5→10, 1→5 sono il bias orario **dell'EURUSD**,
  trovato da Unger scansionando quel cambio. Su un altro strumento non significano niente.
  Portare il **metodo** (scansionare le ore di MGC o MES con `testphase 1` e tenere le
  migliori) sarebbe una strategia nuova con un forte rischio di overfitting: 23 ore × 2 lati
  provate, si tengono le migliori. Unger stesso applica il bias orario all'ES nel modulo 9
  (9x01) e conclude che "non sembra esserci un modo decente per ottenere un risultato
  accettabile".
- **Sul 6E** la numerazione delle barre cambierebbe: la sessione CME parte alle 17:00 CT
  (18:00 New York), un'ora dopo l'apertura del forex spot su cui Unger contava le barre.

**Cosa la riaprirebbe**: un conto che regga un 6E intero con uno stop da $2.000. In quel caso
si testa la versione EURUSD su 6E con la numerazione delle barre spostata di un'ora.
