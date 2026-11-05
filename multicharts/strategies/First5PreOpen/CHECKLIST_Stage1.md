# CHECKLIST Stage 1 — First5 PreOpen

Signal `Mario_First5PreOpen`, da `First5PreOpen.txt`. **Il codice non è mai stato compilato**: il
primo passo è compilarlo in PowerLanguage Editor. Se non compila, dillo al desk.

## Chart

| | |
|---|---|
| Simbolo | `@NQ`, Point Value **$20** |
| Timeframe | **5 min** |
| Sessione | **Globex 17:00–16:00 CT senza pause** |
| Timezone | **Exchange (CT)** |
| Periodo del chart | **2024-08-01 → 2024-12-31** |
| Bar Magnifier | **1 min** |
| Backtesting | Classic, IOG off |
| Commissione | `7.5$ per Contract`, slippage **0** |
| Max bars back | automatico: il codice guarda solo la barra precedente |

**Il periodo è quello della SPEC, non gli ultimi 100 giorni.** Gli ultimi 100 giorni stanno
nell'OOS, che nessuno deve vedere prima della fase 3. Il chart non va allungato oltre il 31/12/2024.

## Run

Report in `strategies/First5PreOpen/reports/`.

| run | `NumContracts` | `ShowLog` | file |
|---|---|---|---|
| A | 1 | 1 | `F5P_S1_A_x1.xlsx` + `F5P_S1_A_log.txt` |
| B | 10 | 0 | `F5P_S1_B_x10.xlsx` |

Gli altri input sono uguali nei due run: `PreOpenFilter 1`, `TP_RR 0`, `TradeStartEL 1240801`,
`TradeEndEL 1241231`.

**Il log.** Prima del run A svuota la scheda Output del PowerLanguage Editor; dopo il run copiala
in `F5P_S1_A_log.txt`.

Niente run con `PreOpenFilter 0` o `TP_RR > 0`: la fase 1 non li chiede, quindi quei due rami del
codice restano non provati. Vale anche per la versione pre-registrata: non li usa.

## Valori per i controlli automatici

| | |
|---|---|
| Orari d'ingresso come li scrive MC | **08:40**, sempre (fill all'open delle 08:35, timbro a fine barra) |
| Trade massimi al giorno | **1** |
| Flat la sera | **sì** |
| Stop in punti | **variabile**: distanza fra il fill e l'altro estremo della 835. Non ha un solo valore, si controlla col log |
| Target in punti | **nessuno** |

```bash
python3 docs/lab.py giudica strategies/First5PreOpen/SPEC.md s1 \
    strategies/First5PreOpen/reports/F5P_S1_A_x1.xlsx \
    --x10 strategies/First5PreOpen/reports/F5P_S1_B_x10.xlsx \
    --entrata 0840-0840 --max-giorno 1 --flat
```

**`--flat` non basta qui.** Lo script guarda se la data cambia. Se `SetExitOnClose` non scatta su
una giornata corta, il trade esce alle 17:10 della stessa data e lo script dice OK. Il controllo 5
sotto va fatto sugli orari di uscita.

## Il log del run A

```
F5P DAY <data> 835 830 O= H= L= C= sgn= 835 O= H= L= C= sgn= dec=<decisione>
F5P ENT <data> 840 dir= entry= stop= dist= tp= open= chiuso=
```

- `dec`: `LONG`, `SHORT`, `NONE-discordi`, `NONE-corpo0`, `NONE-barra`. Con `NONE-barra` la riga ha
  solo l'orario della barra e `prec=`, quello della barra prima.
- Una riga `F5P DAY` per ogni giorno con barre fra le 08:35 e le 15:00, a partire dall'01/08. Se la
  prima riga è più tardi, guarda `Max bars back`.
- `F5P ENT` esce sulla barra del fill. `chiuso=1` vuol dire che lo stop ha già chiuso il trade
  nella barra d'ingresso.

## Controlli

| # | controllo (SPEC, fase 1) | come | atteso |
|---|---|---|---|
| 1 | ingressi solo all'apertura delle 08:35 | `--entrata 0840-0840`; nel log `entry=` uguale a `open=` | tutti i trade alle 08:40, nessuno fuori |
| 2 | verso uguale al segno delle due barre, nessun trade nei giorni discordi | dal log e dalla List of Trades: **5 giorni `LONG`, 5 `SHORT`, 5 `NONE-discordi`**. Rifai i segni dal grafico sulle barre 830 e 835 | long con `sgn=1` su entrambe, short con `sgn=-1` su entrambe, nessun trade nei `NONE`. Ogni riga `F5P ENT` ha un trade e viceversa |
| 3 | stop esattamente sull'altro estremo della 835 | **5 trade a mano**: `stop=` di `F5P ENT` contro `L=` (long) o `H=` (short) della 835 in `F5P DAY`; poi il prezzo d'uscita in List of Trades dei trade chiusi a stop | `stop=` identico all'estremo. Prezzo d'uscita uguale allo stop, o peggio se il prezzo ha saltato il livello: i casi peggiori si annotano |
| 4 | `-SL0` scatta anche sulla barra d'ingresso | nomi d'uscita `F5P-L-SL0` / `F5P-S-SL0`, con ingresso e uscita timbrati 08:40 e `chiuso=1` nel log | almeno qualche caso. Se sono zero, dillo al desk: su una barra da 5 minuti dopo l'apertura è strano |
| 5 | flat alle 15:00 o sull'ultima barra nelle giornate corte | orari di uscita in List of Trades | uscite `F5P-XL` / `F5P-XS` timbrate **15:05** (15:10 se manca la barra delle 15:00). Nelle giornate corte, uscita sull'ultima barra. **Un'uscita dopo le 17:00 è un bug** |
| 6 | massimo 1 trade al giorno | `--max-giorno 1` | OK |
| 7 | test ×10 esatto | `--x10`; in più guarda i trade chiusi da `-SL0` nel run B | stessi ingressi e uscite, P&L ×10 su ogni trade, `Max # Contracts Held` 10. I trade `-SL0` escono con tutti i 10 contratti: quell'ordine parte quando la posizione è ancora flat |
| 8 | solo lunedì–venerdì | giorni della settimana in List of Trades | nessun sabato o domenica |
| 9 | nomi d'uscita | elenco stampato da `giudica` | solo `F5P-L-SL0`, `F5P-S-SL0`, `F5P-L-SL`, `F5P-S-SL`, `F5P-XL`, `F5P-XS` e l'uscita di `SetExitOnClose`. Nessun `-TP` |

Trade attesi: uno ogni due sedute circa, su ~105 sedute. Il numero non è un criterio.

## Giornate da annotare

La SPEC chiede di annotarle in fase 1. Lasciarle dentro è una scelta già scritta: non si tolgono.

| data | giorno | atteso |
|---|---|---|
| 02/09/2024 | Labor Day, cash chiuso | barre 830 e 835 ci sono, il codice tratta il giorno come gli altri. Se c'è un trade, esce sull'ultima barra della mattina |
| 28/11/2024 | Ringraziamento, cash chiuso | come sopra |
| 29/11/2024 | mezza giornata | segnale valido, uscita sull'ultima barra, intorno alle 12:00 CT |
| 24/12/2024 | mezza giornata | come sopra |
| 25/12/2024 | Natale | niente barre 830 e 835: nessun trade e nessuna riga `F5P DAY` |

Per ognuna scrivi se c'è stato un trade e l'orario di uscita.

## Cosa guardare sul grafico

- **Il fuso.** La barra 835 deve essere la prima con il volume del cash: il volume salta lì. Se il
  salto è su un'altra barra il chart non è in CT e il run non vale.
- **Tre trade**, uno chiuso a `-SL0`, uno chiuso a `-SL`, uno uscito alle 15:05: la freccia
  d'ingresso sull'open della barra dopo la 835, e lo stop sul `Low` o `High` della 835.
- **Un giorno `NONE-discordi`**: nessuna freccia, e le due barre di colore opposto.
- **Una giornata corta con un trade**, se c'è: l'uscita sull'ultima barra, non la sera.

## Nota

La fase 1 sta dentro l'IS. I numeri di questi run non sono un giudizio: si legge solo la meccanica.
