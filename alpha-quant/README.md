# alpha-quant

Simulazione e verdetto del laboratorio, sul percorso che porta una strategia da
un'idea al conto live. Legge i dati **solo** da quantlake, in sola lettura.

## Il percorso verso il live

| tappa | dove | cosa decide |
|---|---|---|
| validation (04-12/2025) | `evaluate(spec, strategia, "validation")` | se la strategia merita il suo unico sguardo all'holdout. Conta in `k` |
| holdout (2026) | `evaluate(..., "holdout")`, aperto una volta dal registro | se merita il test in avanti |
| shadow | il trading desk, `mode: shadow` in `strategies.yaml` | il test in avanti, su dati che nessuno ha visto |
| live | il trading desk, `mode: active`, dopo una pull request | soldi veri |

Le prime due tappe sono qui; le ultime due nel desk. Nessun gate di questo
pacchetto promuove a soldi veri.

## Struttura

```
src/alphaquant/
  engine/desk_replay.py   il ciclo del trading desk rigiocato sul passato (livello 2)
  engine/desk_trades.py   i fill del replay come trade da piatto a piatto (SimResult)
  validation/             gate di portafoglio: Sharpe netto, deflated Sharpe con k, drawdown, costi
  registry.py             il registro delle prove, append-only con catena di hash
  evaluate.py             spec -> replay -> gate -> registro, in una chiamata
  calibration/            costi veri e decisioni del desk contro il replay
  instruments/, data/     strumenti, costi, calendari, loader del gold (infrastruttura generica)
config/costs.yaml         costi per strumento e per venue (hyperliquid misurato sui fill veri)
config/splits.yaml        train / validation / holdout
registry/trials.jsonl     ogni spec e ogni run, mai cancellati
scripts/                  confronto delle decisioni live con il replay
legacy/                   codice del corso originale, solo come riferimento
```

## Uso

```bash
poetry install
poetry run pytest
```

Le strategie si portano in validation dalla fabbrica (`../factory`, skill
`/quant-factory`), non a mano: così ogni prova entra nel registro.
