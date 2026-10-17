# CHECKLIST Stage 1 — ESCounter

## Primo giro (18/10/2026) — **invalido: chart a 5 minuti invece che a 30**

`check_report.py` legge `Compression: 5 Minutes`, e il log lo conferma: segnali alle 08:45,
18:35, 04:50, orari che su barre a 30 min non esistono. La regola d'ingresso è "il **close a
30 minuti** torna sopra il minimo di ieri": su barre a 5 min l'incrocio scatta su chiusure
diverse e più frequenti, quindi **non è la strategia di Unger**. I numeri sotto non valgono
come misura; i report non sono conservati.

Periodo: 2026‑08‑11 → 2026‑10‑16 (66 giorni). @ES, $15/contratto, Bar Magnifier 1 min.

### Cosa questo giro ha comunque verificato (vale anche a 30 min)

| # | controllo | esito |
|---|---|---|
| 1 | `MyLow` = minimo della sessione appena chiusa | ✅ confrontato con le barre `1d_cme` di quantlake: identico al centesimo in 8 sessioni su 9. Le righe di **domenica 17:30** usano il minimo del **venerdì** (verificato su 14/08 e 21/08): corretto. Il 20/08 il chart ha 7.725,50 e quantlake 7.726,75 (5 tick): differenza di dato fra il chart e il nostro export a 1 min, non di logica |
| 2 | data2 con lo stesso template di data1 | ✅ di conseguenza: il minimo è quello della sessione Globex 17:00–16:00, non della sola sessione cash |
| 4 | stop e target | ✅ run A: **20 `Stop Loss` a −14,00 pt esatti, 14 `Profit Target` a +30,00 pt esatti**, nessun'altra uscita. Il rapporto vincita/perdita realizzato è **2,01** (1.470 / 730): quello nominale. L'1,04 di Unger **non si riproduce**: nel suo backtest c'era qualcosa che il codice del video non mostra |
| 5 | variante B | ✅ flat a fine sessione: 6 uscite `End of Day Exit` alle 16:00, quella del 07/09 (Labor Day, sessione corta) alle 12:00. **Mai più di 2 ingressi per sessione** (11 sessioni con 1, 9 con 2) |
| 6 | variante A, rischio overnight | in 66 giorni 1 trade oltre le 23 ore (31 ore), nessuno nel weekend. Ingressi per sessione fino a **4** (11 × 1, 5 × 2, 3 × 3, 1 × 4): senza tetto il worst day non è limitato |
| 7 | scala ×10 | ✅ A10 = 10 × A su tutti i 34 trade |

### Numeri (non validi: timeframe sbagliato)

| run | n | WR | avg | PF |
|---|---|---|---|---|
| A | 34 | 41,2% | +$176 | 1,41 |
| B | 29 | 34,5% | −$65 | 0,85 |

## Per il secondo giro
Stesso periodo, **data1 a 30 minuti** (data2 resta a 1440). Rifare A, A10 e B con il log su B.
Da chiudere: controllo 2 (ingressi sulle chiusure a 30 min: orari dei segnali solo :00 e :30)
e 3 (nessuna entrata fra 15:30 e 17:30).
