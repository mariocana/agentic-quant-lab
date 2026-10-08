# Journal discrezionale

Registro dei trade/decisioni discrezionali, strutturato come **dataset** (non un diario):
ogni riga ha campi fissi, così dopo 50‑100 decisioni puoi misurare hit‑rate, R medio,
expectancy e drawdown — anche **per categoria di tesi** — con la stessa disciplina degli EA.

## Regole d'uso
- Una riga per decisione. **Stop e target si scrivono PRIMA** di entrare.
- Tieni il discrezionale separato dal sistematico (conto o ledger diverso).
- Size minima o paper all'inizio: l'obiettivo è il track record, non il P&L.
- Nessuna conclusione prima di **~50 decisioni** (lo script lo ricorda).

## File
- `trades.csv` — il journal (le due righe d'esempio si possono cancellare).
- `journal_stats.py` — statistiche: `python3 journal_stats.py` (o `python3 journal_stats.py altro.csv`).

## Campi di `trades.csv`
| Campo | Cosa mettere |
|---|---|
| `date` | data della decisione, `YYYY-MM-DD` |
| `instrument` | es. `NAS100`, `EURUSD` |
| `direction` | `long` / `short` |
| `category` | tipo di tesi: `macro`, `tecnica`, `evento`, `sentiment`, `altro` |
| `horizon` | orizzonte dichiarato: `intraday`, `giorni`, `settimane` |
| `thesis` | la tesi in una frase |
| `confidence` | 1 (bassa) · 2 · 3 (alta), decisa **al momento** dell'ingresso |
| `entry` | prezzo d'ingresso |
| `stop` | stop deciso prima |
| `target` | target deciso prima |
| `size` | size (lotti/contratti) — informativa |
| `exit` | prezzo di uscita (vuoto se ancora aperto) |
| `result_r` | esito in R; **se vuoto lo calcola lo script** da entry/stop/exit |
| `note` | "cosa non avevo visto" — la lezione |

**R** = profitto ÷ rischio iniziale (`|entry − stop|`). Un trade chiuso a target con
rapporto 1:2 vale `+2R`; uno stoppato vale `−1R`. Ragionare in R rende confrontabili
trade su strumenti e size diversi.

## Cosa guardare nel report
- **Expectancy (R medio)**: > 0 e stabile è l'unica cosa che conta nel lungo periodo.
- **Per categoria**: dove hai davvero un edge? (spesso non dove credi).
- **Per confidenza**: se i trade "confidenza 3" non rendono più dei "1", la tua
  sensazione di certezza non è informativa — utile saperlo.
- **Max drawdown in R**: quanto devi essere pronto a sopportare.
