# Conti live

Un conto, una riga di `conti.csv` e una cartella `AAAA-MM-GG_prop_book/`. Il riepilogo:

```bash
python3 docs/live_conti.py
```

**Quando si apre un conto:** riga nuova con `esito` = `aperto`, e cartella nuova.

**In ogni cartella:**
- `report_grafico_*.xlsx`: il Performance Report del grafico, uno per strategia;
- `ordini.csv` e `logs.csv`: le schede Orders e Logs dell'Order and Position Tracker;
- `dashboard_*.png`: la dashboard della prop a fine run;
- `note.md`: giorno per giorno, conto contro grafico.

**Quando si chiude:** `fine`, `esito` e i numeri in `conti.csv`.

| esito | quando |
|---|---|
| `aperto` | eval in corso |
| `pass` | eval passata |
| `fail` | MLL o scadenza |
| `fail da confermare` | i log dicono fail, manca la dashboard |
| `funded` / `funded chiuso` | conto funded vivo / finito; `payout_usd` è il totale incassato |

`costo_usd` è quanto addebitato davvero, in dollari; il dettaglio contabile in euro resta in
`journal/cost_report/`. Una riga conta come pass se l'eval è stata passata, anche se poi il
funded è morto.
