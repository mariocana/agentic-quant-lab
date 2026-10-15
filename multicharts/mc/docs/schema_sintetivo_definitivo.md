Nove stage, ma sono cinque domande. Una strategia alla volta.

fase	la domanda	criterio	se fallisce
1.	Scrivi (0–1)	il codice fa quello che credo?	100 gg: trade dove previsto, flat la sera, P&L ×10	si corregge, non è un kill
2.	Misura (2)	l’edge esiste?	2020–24: t ≥ 2 · WR ≥ 55% · R:R 0,5–1	cimitero
3.	Falsifica (5–6)	regge fuori campione?	2025–26, una volta sola: t ≥ 1,3	cimitero, definitivo
4.	Decidi (7)	l’edge basta per questo conto?	simulatore: pass rate cumulato sui tentativi	cimitero
5.	Deploy (8–9)	regge in esercizio?	paper 1 settimana, poi eval	si spegne

Lo Stage 4 (migliorie) è opzionale fra la 2 e la 3. Lo Stage 8 (basket) serve solo quando le vive sono più di una.

Le due regole che contano più dei criteri:

1. L’OOS si gira una volta sola. Se lo rigiri con parametri diversi non è più un OOS, è un secondo in-sample.

2. Soglia, attesa e kill si scrivono in SPEC.md prima del run. Altrimenti il numero lo si spiega sempre.

Cosa non sta più in pipeline:

3. PF ≥ 1,2 · avg ≥ $70 · nessun anno > 50% → metodologia live, stand-by.
4. Il RATIO e il vecchio Gate 3 → sostituiti dal simulatore. Trattavano la eval come «sopravvivere a cinque anni» invece che come primo passaggio ripetibile.
5. Le due frasi: t dice se l’edge esiste, non se basta. · Il rischio è un output, non un input.

Fase 2 = Stage 2 = Backtest IS = in-sample = 2020–2024.

1. IS (In Sample) = i cinque anni su cui misuri. Qui hai il diritto di provare varianti, filtri, parametri. 2020–2024.

2. OOS (Out Of Sample) = i mesi che non hai mai guardato. 2025–2026. Si usa una volta, con i parametri già congelati sull’IS.

3. Perché serve la separazione: se provi 20 varianti sull’IS, la migliore sembra buona anche se è fortuna — hai pescato il rumore. L’OOS è l’unico posto dove il numero non può essere stato fittato, perché quando hai deciso i parametri quei dati non li avevi visti.

4. Nella pipeline: fase 2 misura (t ≥ 2 sull’IS), fase 3 falsifica (t ≥ 1,3 sull’OOS). La soglia scende perché l’OOS ha meno trade, quindi barra d’errore più larga.



---

# Che script far partire, fase per fase

Tutto da `/Users/mario/Documents/Repo/my-codes`. Solo libreria standard: niente da installare.

## Fase 1 — Scrivi (Stage 0-1)

Nessun criterio da calcolare, si legge l'Output Window. L'unica cosa da verificare col codice
e il test ×10: girare a 1 contratto e a 10, esportare due report e confrontarli.

```bash
python3 mc/docs/check_report.py mc/strategies/NOME/reports/*_S1_*.xlsx --tabella
```

`n`, `WR%` e `R:R` devono essere **identici** fra i due; `avg` deve stare a ×10.

## Fase 2 — Misura, IS 2020-2024 (Stage 2)

```bash
python3 mc/docs/check_report.py mc/strategies/NOME/reports/NOME_S2_IS.xlsx --fase 2
```

Guarda **prima** i CONTROLLI PRELIMINARI: se la commissione e a zero o il Bar Magnifier e
disattivato, i numeri sotto non valgono e il run si rifa.

**Annota la riga `DD chiusi`**: serve alla fase 3.

## Fase 3 — Falsifica, OOS 2025-2026 (Stage 5)

```bash
python3 mc/docs/check_report.py mc/strategies/NOME/reports/NOME_S5_OOS.xlsx --fase 3 --dd-is 31670
```

`--dd-is` e il `DD chiusi` stampato dalla fase 2. Senza, il criterio sul drawdown non viene
confrontato e lo script lo dice.

**Una volta sola.** Se lo rigiri con parametri diversi non e piu un OOS.

## Fase 4 — Decidi (Stage 7)

```bash
python3 mc/docs/prop_sim.py mc/strategies/NOME/reports/NOME_S5_OOS.xlsx
```

Si legge in quest'ordine:

1. **STATO ATTUALE** — se siamo oltre il 95esimo percentile del drawdown, e il momento
   sbagliato per partire (Live 004).
2. **PASS RATE** — la colonna **iid** e quella su cui si decide. Il contiguo sopravvaluta.
3. Il numero di micro **migliore e un output**, non una scelta.

Opzioni che contano:

```bash
--giorni-max 250      # Lucid non ha limite di tempo: 60 e un'assunzione, va testata
--comm-micro 2.50     # sensibilita' ai costi del micro (default 1,50/round-turn)
--micro 1,2,3,4,6,8   # la griglia da scandire
--sim 20000           # numero di simulazioni
```

## Confronto rapido di piu varianti

```bash
python3 mc/docs/check_report.py mc/strategies/*/reports/*.xlsx --tabella
```

Una riga per report con n, WR, R:R, t, PF, avg. E cosi che si vede se una variante regge o se
il t alto stava solo su un campione piccolo.

## Cosa NON esiste ancora, e va fatto a mano

- **Stage 6 (bootstrap)**: nessuno script. Il `t` della fase 2/3 risponde quasi alla stessa
  domanda, e per questo lo Stage 6 e stato saltato su DriftPullback.
- **Stage 8 (basket)**: nessuno script. La correlazione fra due strategie si e calcolata a
  mano sulle liste di trade; serve almeno una seconda strategia **con un OOS valido** prima
  che abbia senso scriverlo.
- **Stage 9 (paper/deploy)**: niente da calcolare.

## I due numeri da ricordare

- **t** = avg trade / barra d'errore. Dice se l'edge **esiste**, non se **basta**.
- **pass rate** = dice se basta. Si legge **cumulato sui tentativi**: 42% per tentativo fa
  89% entro quattro, e quattro tentativi costano $400.
