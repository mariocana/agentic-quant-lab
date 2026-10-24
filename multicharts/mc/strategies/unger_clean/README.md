# Unger — Trading System Supremacy: codici ripuliti

I codici del corso in `education/unger/Trading System Supremacy/13. Codici` sono stati
trascritti da screenshot dei video e non compilano (refusi OCR, `:` al posto di `;`, righe
tagliate). Qui li riscriviamo **uno alla volta**, ricostruendoli dal codice che si vede nei
video (fotogrammi estratti con `ffmpeg`), e ognuno entra nella pipeline prop dallo Stage 0.

Regole per ogni codice:
- **Fonte primaria = il fotogramma del video**, non il file trascritto. Si cita il video e il
  secondo in cui il codice è leggibile.
- La versione **A** è fedele all'originale (stessi parametri finali di Unger). Ogni modifica
  per la prop è una variante separata, pre‑registrata nella spec.
- I periodi successivi alla registrazione del corso (2016) sono **dati mai visti** dall'autore:
  i parametri si congelano a quelli del video e non si riottimizzano.

| # | strategia | fonte | stato |
|---|---|---|---|
| 1 | **ESCounter** | modulo 9, video 9x04 e 9x05 | **cimitero, causa A** (18/10/2026): IS 2020–2024 t −2,02, perde anche prima dei costi |
| 2 | `PtnBaseSA` (funzione dei pattern) | video 4x01 (codice) + modulo 3 (slide) | **Gate 1 passato** (18/10/2026): 40 pattern su 95 sessioni identici al ricalcolo |
| 3 | Trend Following (`Develop`) | modulo 4 (4x01–4x04) + `13. Codici/Trend Following/Develop` | **prossimo**. Breakout del massimo/minimo del giorno filtrato dai pattern, forex 15 min (parametri finali nei commenti: pattern 6/4/18/19, 04:00–13:30, stop 0,011, target 0,035). Strumento da leggere nel video |
| 4 | **Counter Trend** (`DevelopRev`, GBPUSD 30 min) | video 5x01 (codice) e 5x02 (parametri) | **cimitero, causa A** (rifatto il 24/10/2026 con il chart di GC in ora di New York, template 18-17 e `MyStartTime 300`): GC A t 0,31, GC B t −1,15 (negativo anche lordo). ES e YM senza edge (migliore YM B t 1,01) |
| 5 | **Gap** (`GoldGapper`) | video 7x01 e 7x02 + `GapsFunctions.pla` | **cimitero, causa A** (24/10/2026): IS 2020–2024 A t 0,48 (94 trade), B t −0,59 (50 trade, negativo anche lordo). Troppo pochi trade comunque per la prop |
| 6 | **BIAS** (`DevelopBIAS`, `DevelopBIASEURUSDFineTune`) | video 6x01 e 6x03 + screenshot dei settaggi | **trascritta e archiviata senza run** (23/10/2026): EURUSD 60 min, su Lucid solo 6E intero con stop di 160 pip = $2.000 = MLL; bias orario non portabile |
| 7 | Dax FirstHour, Night FIB | `0. Risorse/MC-TS` (già puliti) | **archivio, non testate** (24/10/2026): trascritte in `DaxFirstHour/` e `NightFIB/`; DAX (Eurex) e FTSE MIB (IDEM) non sono tradabili sulle prop. Daily Factor non è una strategia: è la funzione `abs(C − O) / (H − L)` del giorno, usata come filtro in Dax FirstHour |
| 8 | IntraToOverNight | `12. Materiale extra/12x04.3` | **non è una strategia**: è il `Develop` del Trend Following con un'uscita in più (se alle 16:45 il trade è in guadagno lo tiene la notte). Da valutare come variante del n. 3, solo se il 3 ha un edge |
| 9 | Stop Progressivi | `12. Materiale extra/12x04.2` | **non è una strategia**: modulo d'uscita (stop e target che si stringono ogni giorno in posizione) su un ingresso a pattern alle 16:00. Variante d'uscita, come il n. 8 |
| 10 | FXFader | `12. Materiale extra/12x02.1` (Trade Navigator) | da fare: 6B 60 min, rientro sopra il minimo / sotto il massimo del giorno se il range di oggi è sotto quello di ieri, stop 100 tick. Parente stretto di ESCounter (morto, causa A); su 6B lo stop è $625 a contratto, causa B |
| 11 | WeeklyBump | `12. Materiale extra/12x02.2` (Trade Navigator) | da fare per ultimo: barre **settimanali** su un paniere di 67 futures, breakout della settimana di indecisione, uscita a fine settimana. Tiene le posizioni giorni interi: contro "flat prima della chiusura" per costruzione |

Nota: i file `9x02` e `9x03` del modulo 9 sono **lo stesso video** (stesso md5): manca la
parte 3 originale.
