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
| 3 | Trend Following (`Develop`) | modulo 4 / 9x02 | da fare, dopo `PtnBaseSA` |
| 4 | **Counter Trend** (`DevelopRev`, GBPUSD 30 min) | video 5x01 (codice) e 5x02 (parametri) | **cimitero, causa A** (23/10/2026): su GC B perde anche lordo (t −2,19); ES e YM non la salvano (migliore YM B t 1,01). 6B non testato: causa B per costruzione |
| 5 | **Gap** (`GoldGapper`) | video 7x01 e 7x02 + `GapsFunctions.pla` | Stage 0: spec e codice su @GC 5 min; funzioni dal `.pla` (il `_DayDefinition.txt` è una versione che non fa trade) |
| 6 | **BIAS** (`DevelopBIAS`, `DevelopBIASEURUSDFineTune`) | video 6x01 e 6x03 + screenshot dei settaggi | **trascritta e archiviata senza run** (23/10/2026): EURUSD 60 min, su Lucid solo 6E intero con stop di 160 pip = $2.000 = MLL; bias orario non portabile |
| 7 | Dax FirstHour, Night FIB | `0. Risorse/MC-TS` (già puliti) | solo da portare nella pipeline |

Nota: i file `9x02` e `9x03` del modulo 9 sono **lo stesso video** (stesso md5): manca la
parte 3 originale.
