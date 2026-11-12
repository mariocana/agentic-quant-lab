# Unger Academy — Strategie Trend Following sul Nasdaq (trascritte, mai girate)

**Fonte:** `NasdaqRegoleUngerAcademy.pdf` (copia in questa cartella), PDF gratuito della Unger Academy (4 pagine, nessun
periodo né risultato dichiarato). Port MQL5 in `ingest/mql5/unger/nasdaq/`. Codice MultiCharts:
`UngerNasdaq.txt`, da salvare come `Mario_UngerNasdaq`, **mai compilato né girato**.

## ⚠️ Disclaimer: le posizioni attraverso la pausa delle 16:00–17:00 CT

Tutte e due le strategie tengono posizioni **oltre la chiusura delle 16:00 CT** (Strategia 1
fino a 8 giorni, weekend compresi; Strategia 2 fino a 1 giorno, con ingressi notturni). **Sulle
prop la posizione aperta nella pausa 16:00–17:00 CT non è possibile: la chiudono.** Da
verificare per conto (Lucid, FTMO via bridge) nella pipeline e in `docs/go_live.md` prima di
qualunque run per il live. Se la chiusura è forzata, le regole vanno riscritte come intraday,
e allora è un'altra strategia.

## Le regole del PDF

| | Strategia 1 | Strategia 2 |
|---|---|---|
| timeframe | 15 min, orario exchange | 15 min, orario exchange |
| long | C > SMA(65) e C incrocia al rialzo il massimo di ieri − 10 | C > apertura + 6 × ATR(200) e Momentum(50) > 20 |
| short | C < SMA(5) e C incrocia al ribasso il minimo di ieri − 35 (formula) / + 35 (testo) | C < apertura − 8,5 × ATR(200) |
| finestra | 11:00–15:00 | long 17:15–14:00, short 21:00–12:00 |
| uscite | stop $1.300, target $3.000, max 8 giorni | stop $600, target $2.000, break-even $600, max 1 giorno |

**Il PDF si contraddice sullo short della Strategia 1:** la formula è `lowd1-35`, il testo dice
"minimo della sessione precedente più 35 punti". Nel codice: input `ShortTesto`.

## Misura proxy (10/11/2026), non un backtest MultiCharts

NQ a 1 minuto di quantlake, IS 2020–2024, ora CT, $15 a giro, posizione tenuta come da regole
(attraverso la pausa delle 16:00 e i weekend, cioè **senza** il vincolo del disclaimer). Per micro:

| | n | WR | avg | t | long | short |
|---|---|---|---|---|---|---|
| S1, short alla formula (min − 35) | 397 | 35,0% | +$19 | 1,85 | +$33 | +$3 |
| S1, short al testo (min + 35) | 447 | 35,6% | +$21 | 2,20 | +$35 | +$9 |
| controllo: long ogni giorno alle 11:00, stesse uscite | 1.115 | 32,4% | +$7,5 | 1,25 | | |
| controllo: short ogni giorno alle 11:00 | 1.160 | 28,4% | −$9,6 | −1,69 | | |
| S2 | 1.899 | 18,1% | +$4 | 1,94 | +$6 | −$0,5 |
| controllo: long ogni giorno alle 09:00, stesse uscite | 1.284 | 15,5% | −$2,6 | −1,04 | | |

- S1 batte il controllo di ~$25 per micro sui long e ~$13–19 sugli short; positiva in tutti e
  cinque gli anni. S2 è debole.
- **Cautele:** parametri asimmetrici, quasi certamente ottimizzati dall'autore su un periodo non
  dichiarato (probabilmente il nostro IS); le due letture dello short sono già k = 2; misura su
  dati a 1 minuto. Se si porta in `/lab`: via B, versione "formula" pre-registrata, OOS
  asimmetrico, e prima il disclaimer.
