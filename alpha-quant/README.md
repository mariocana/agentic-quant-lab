# alpha-quant

Motore di backtest e validazione di strategie multi-asset (prima crypto e futures
CME, poi forex e azioni). Legge i dati **solo** da quantlake, in sola lettura, e
non scarica né scrive dati.

Progetto completo: documento "alpha-quant — Motore di backtest e validazione
multi-asset". Stato: fase 1 (fondamenta).

## Struttura

```
src/alphaquant/
  config.py        QUANTLAKE_DATA_ROOT e file dei costi
  data/            loader del gold (sola lettura), controllo schema, report di qualità
  instruments/     Instrument, costi configurabili, calendari di sessione, InstrumentSource
  engine/          tipi comuni ai due livelli di simulazione (Trade, SimResult)
config/costs.yaml  commissioni e slippage per strumento (valori da verificare)
legacy/            codice originale del corso, solo come riferimento
```

## Da dove arrivano i dati

| Cosa | Dove | Chi lo scrive |
| --- | --- | --- |
| Candele | `<QUANTLAKE_DATA_ROOT>/gold/<gold_table>/<timeframe>` | quantlake |
| Specifiche degli strumenti | `<QUANTLAKE_DATA_ROOT>/reference/instruments` | quantlake |
| Costi (commissioni, slippage) | `config/costs.yaml` | tu |

I timeframe sono allineati a UTC (`15m`, `1d`) oppure, per i futures CME, alla
sessione Globex con il suffisso `_cme`: `1d_cme` ha una barra per sessione, aperta
alle 17:00 di Chicago, e il report di qualità conta le sessioni mancanti.

`QUANTLAKE_DATA_ROOT` ha come default `../quantlake/data`. Ogni lettura registra la
versione Delta, così un test si può rifare identico con `version=...`.

## Uso

```python
from datetime import datetime

from alphaquant.instruments import QuantlakeInstrumentSource
from alphaquant.data import load_bars

es = QuantlakeInstrumentSource().get("ES")
bars = load_bars(es, "15m", start=datetime(2024, 1, 1))
print(bars.delta_version, bars.quality.summary())
```

## Sviluppo

```
poetry install
poetry run pytest
```
