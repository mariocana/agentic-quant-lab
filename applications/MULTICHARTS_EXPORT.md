# Export da MultiCharts (TradeStation) per quantlake

Vale per i continui @ES / @NQ (`ES_1min.csv`, `NQ_1min.csv`) e per i singoli
contratti (`ESZ25_1min.csv`, `NQH26_1min.csv`). L'indicatore è
`applications/ExportBars_multicharts.txt`.

## Sessione

Usa una sessione **17:00–16:00 CT senza pause** (domenica–venerdì), non un
template di MultiCharts già pronto: quello usato fino a ottobre 2026 tagliava
15:15–15:30 CT da lunedì a giovedì (pausa abolita dal CME il 28/06/2021) e
chiudeva il venerdì alle 15:15 CT. La pausa giornaliera 16:00–17:00 CT è la
sola assenza attesa.

## Passi

1. **QuoteManager** → clic destro nell'elenco → **Add Symbol** → **From Data
   Source** → **TradeStation**. Cerca il simbolo (`@ES`, oppure il contratto,
   es. `ESZ25`); se la ricerca non mostra i contratti scaduti, scrivi il codice
   per intero. Seleziona → **OK**.
2. **File → New → Chart Window**: data source TradeStation, il simbolo, **1
   Minute**.
   - **Session**: la sessione 17:00–16:00 CT senza pause descritta sopra.
   - **Time Zone**: **Exchange** (Chicago). quantlake legge i CSV come ora di
     Chicago (`chart_tz` in `applications/symbols.py`); con il fuso del PC i
     timestamp sono sfasati.
   - **Range**: "From date". Per @ES tutta la storia; per un contratto almeno
     dalle 3 settimane prima del suo roll fino a qualche giorno dopo.
3. **Insert → Study → ExportBars**. In **Format Study → Inputs** imposta
   `FilePath` a `\\<IP del Mac>\multicharts\<nome>_1min.csv`, con `<nome>` =
   `ES`, `NQ` o il codice del contratto (`ESZ25`).
4. Aspetta che tutta la storia sia caricata: l'indicatore scrive ogni barra
   chiusa. Per un contratto scaduto il file è completo a fine caricamento:
   togli l'indicatore o chiudi il grafico (ExportBars cancella il file quando
   viene ricalcolato, non lasciarlo su altri grafici con lo stesso FilePath).
   Per @ES / @NQ lascialo attivo: aggiunge una riga a ogni barra chiusa.
5. Controlla il file sul Mac (`python/quantlake/data/multicharts/`):
   - intestazione `date,time,open,high,low,close,volume,ticks,upticks,downticks`;
   - `time` è l'ora di **chiusura** della barra (HHMM, Chicago);
   - **il venerdì l'ultima barra deve essere quella delle 15:59 CT**, cioè la
     riga con `time` = `1600`. Se l'ultima è `1515`, il template taglia ancora;
   - nessun buco fisso 15:15–15:30 da lunedì a giovedì (righe `1516` … `1530`
     presenti);
   - per un contratto: prima e ultima data coprono il roll (ESZ25: giorno di
     roll giovedì 11/12/2025, cambio mercoledì 10/12 alle 17:00 CT).
6. Sul Mac:
   - @ES / @NQ riesportati: `.venv/bin/python applications/historical/multicharts.py --replace`
     poi `.venv/bin/python applications/historical/ohlcv_gold.py` (ricostruisce
     il gold da zero) e `daily_context.py`. Lo script avvisa se trova ancora
     buchi ricorrenti o venerdì corti; il dettaglio è in
     `applications/diagnostics/multicharts_gaps.py ES`.
   - contratti: `.venv/bin/python applications/historical/multicharts_rolls.py`.
