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
| 1 | **ESCounter** | modulo 9, video 9x04 e 9x05 | Stage 0 — spec e codice scritti |
| 2 | `PtnBaseSA` (funzione dei pattern) | moduli 3–6 + `12x03 pattern base reference.docx` | da fare: serve a Trend Following, Counter Trend, Gap, BIAS |
| 3 | Trend Following (`Develop`) | modulo 4 / 9x02 | da fare, dopo `PtnBaseSA` |
| 4 | Counter Trend (`Develop`, GBPUSD 30 min) | modulo 5 | da fare, dopo `PtnBaseSA` |
| 5 | Gap (`GoldGapper`, `MyGapFinder`) | modulo 7 + `GapsFunctions.pla` | da fare |
| 6 | BIAS (`Develop`, `DevelopEURUSDFineTune`) | modulo 6 + screenshot dei settaggi | da fare, dopo `PtnBaseSA` |
| 7 | Dax FirstHour, Night FIB | `0. Risorse/MC-TS` (già puliti) | solo da portare nella pipeline |

Nota: i file `9x02` e `9x03` del modulo 9 sono **lo stesso video** (stesso md5): manca la
parte 3 originale.
