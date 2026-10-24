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
| 3 | **Trend Following** (`DevelopFineTune` 4x03, `DevelopID` 4x04) | video 4x03 (codice al 9:50) e 4x04 (codice allo 0:40) | **Stage 0** (24/10/2026): EURUSD 15 min nei video. A = multi‑day, B = intraday. Replica su 6E (causa B per costruzione, misura l'edge) + porting su GC, ES, NQ con stop in % (0,83% / 0,56%). Stage 1 da lanciare |
| 4 | **Counter Trend** (`DevelopRev`, GBPUSD 30 min) | video 5x01 (codice) e 5x02 (parametri) | **cimitero, causa A** (rifatto il 24/10/2026 con il chart di GC in ora di New York, template 18-17 e `MyStartTime 300`): GC A t 0,31, GC B t −1,15 (negativo anche lordo). ES e YM senza edge (migliore YM B t 1,01) |
| 5 | **Gap** (`GoldGapper`) | video 7x01 e 7x02 + `GapsFunctions.pla` | **cimitero, causa A** (24/10/2026): IS 2020–2024 A t 0,48 (94 trade), B t −0,59 (50 trade, negativo anche lordo). Troppo pochi trade comunque per la prop |
| 6 | **BIAS** (`DevelopBIAS`, `DevelopBIASEURUSDFineTune`) | video 6x01 e 6x03 + screenshot dei settaggi | **trascritta e archiviata senza run** (23/10/2026): EURUSD 60 min, su Lucid solo 6E intero con stop di 160 pip = $2.000 = MLL; bias orario non portabile |
| 7 | Dax FirstHour, Night FIB | `0. Risorse/MC-TS` (già puliti) | **archivio, non testate** (24/10/2026): trascritte in `DaxFirstHour/` e `NightFIB/`; DAX (Eurex) e FTSE MIB (IDEM) non sono tradabili sulle prop. Daily Factor non è una strategia: è la funzione `abs(C − O) / (H − L)` del giorno, usata come filtro in Dax FirstHour |
| 8 | IntraToOverNight | `12. Materiale extra/12x04.3` | **riscritto e archiviato** (24/10/2026) in `IntraToOverNight/`: il `Develop` con un'uscita in più (se alle 16:45 il trade guadagna, resta aperto la notte). Contro "flat prima della chiusura" |
| 9 | Stop Progressivi | `12. Materiale extra/12x04.2` | **modulo d'uscita, tenuto a disposizione** (24/10/2026) in `StopProgressivi/`: stop e target che si riducono di una percentuale per ogni giorno in posizione. Con i fattori a 0 restano fissi |
| 10 | FXFader | `12. Materiale extra/12x02.1` (Trade Navigator) | **riscritto in PowerLanguage e archiviato** (24/10/2026) in `FXFader/`: 6B 60 min, stop 100 tick = $625 a contratto (causa B), stessa idea di ESCounter (causa A) |
| 11 | WeeklyBump | `12. Materiale extra/12x02.2` (Trade Navigator) | **riscritto in PowerLanguage e archiviato** (24/10/2026) in `WeeklyBump/`: barre settimanali su 67 futures, posizione tenuta tutta la settimana |

Nota: i file `9x02` e `9x03` del modulo 9 sono **lo stesso video** (stesso md5): manca la
parte 3 originale.
