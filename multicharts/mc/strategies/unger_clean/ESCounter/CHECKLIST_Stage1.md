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

---

## Secondo giro (18/10/2026) — 30 minuti giusti, **ma session template ancora vecchio**

Periodo 2026‑08‑17 → 2026‑10‑16 (60 giorni), data1 @ES 30 min. **Gate 1 non ancora passato**
per un solo motivo: il chart ha la **pausa 15:15–15:30** (template pre‑2021).

**La prova.** Il log ha un segnale alle **15:15** (15/09). Con barre a 30 min ancorate alle
17:00 una barra che chiude alle 15:15 esiste solo se la sessione si ferma alle 15:15 e
riparte alle 15:30. In List of Trades quel segnale entra nella barra 15:30–16:00, e nella
variante B esce **nella stessa barra** a fine sessione: un trade artefatto. Anche il 08/10 c'è
una barra 15:00–15:15. È lo stesso template che tagliava l'export di @ES in quantlake.

| # | controllo | esito |
|---|---|---|
| 1 | `MyLow` | ✅ identico al primo giro su tutte le sessioni |
| 2 | segnali sulle chiusure a 30 min | ✅ tutti a :00 o :30, **tranne il 15:15** (template) |
| 3 | nessuna entrata fra 15:30 e 17:30 | ❌ una (15/09, barra 15:30–16:00), causata dal template |
| 4 | stop e target | ✅ A: 12 `Stop Loss` a −14,00 e 9 `Profit Target` a +30,00, nient'altro |
| 5 | variante B | ✅ 6 `End of Day Exit` alle 16:00 (Labor Day alle 12:00), max 2 ingressi per sessione (10 × 1, 5 × 2) |
| 6 | variante A | 1 trade oltre le 23 ore (34 ore 30), nessuno nel weekend; fino a 3 ingressi per sessione |
| 7 | scala ×10 | ✅ A10 = 10 × A su tutti i 21 trade |

Nota sulla List of Trades: con Bar Magnifier MC timbra l'entrata con l'ora di **chiusura**
della barra (segnale 10:30 → entrata "11:00"), ma il prezzo è l'open della barra: normale.

## Per il terzo giro
Solo il session template, **su data1 e su data2**: domenica–venerdì **17:00–16:00 CT, nessuna
pausa** (Format Instrument → Sessions, oppure un template personalizzato). Poi A e B sullo
stesso periodo. Il venerdì l'ultima barra deve chiudere alle **16:00**, e nel log non deve
più comparire nessun `t= 1515`.
