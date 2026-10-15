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


