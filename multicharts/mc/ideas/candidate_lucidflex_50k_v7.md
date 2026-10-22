<!-- researcher.py, 20/10/2026, model claude-sonnet-5-5, effort medium, TEST -->

# Ricerca del 20/10/2026: nessuna candidata nuova

**Esito.** Non consegno candidate né quasi-candidate. Ho aperto una sola fonte tra quelle DA LEGGERE, e non produce una regola tradabile. Non ho letto altro. Preferisco dirlo piuttosto che costruire candidate a tavolino, come chiede il prompt.

## Tabella di sintesi

| # | Nome | Strumento · TF | Famiglia | Stop (punti → $/micro) | n/anno | WR | R:R | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| – | nessuna | – | – | [manca] | [manca] | [manca] | [manca] | – | – |

## Cosa ho fatto

1. **Fonte aperta.** Ho aperto [Choi-Larsen-Seppi, *Equilibrium Effects of Intraday Order-Splitting Benchmarks*](https://arxiv.org/abs/1803.08336), che era DA LEGGERE.
   - È un modello teorico in tempo continuo. Prevede pattern prevedibili di pressione sul prezzo dovuti ai benchmark TWAP e VWAP.
   - Livello 3, cioè affermato senza test su dati. Non contiene regole, orari, stop o costi. Non è testato su futures e non riporta costi.
   - Può motivare un'ipotesi sul flusso, ma non è una strategia. Scartata.
2. **Fonte non aperta.** Intraday Patterns in the Cross-section of Stock Returns (arXiv 1005.3535) è rimasta DA LEGGERE. È cross-section su azioni e fallisce quasi certamente il filtro 1, ma non l'ho aperta e non la giudico.
3. **Altro non letto.** Non ho letto le altre fonti DA LEGGERE (MOC imbalance, VWAP, M2K ecc.), perché nessuna è una fonte primaria testata. Restano aperte.

## Osservazioni sui documenti, utili per la prossima ricerca

- **DriftPullback su YM è già stata provata.** `ricerca_18-10.md` la elenca come "un run" ancora da fare. Nei REPORT MISURATI esiste `DPB_S2_IS_PORT-YM_2020-2024`: n = 3393, t = 0,2, WR 61,8%, avg $1,54. L'edge non si trasferisce. Non è un'idea nuova e non va riproposta.
- **Altri port già misurati su altri strumenti.**
  - BTC First30 ha t negativo su tutte le varianti.
  - ON_Reversal ha t = −2,24 su 1.661 trade.
  - Entrambe sono già nel cimitero.
- **LastHalfHour non ha ancora report misurati.** Passa il filtro paper. Il suo punto debole è che il paper non considera i costi.
  - Non è un'idea nuova. Se la si testa, bisogna controllare la frequenza ($/giorno per micro).
  - Il database scarta lavori affini perché l'uscita è alla chiusura, senza target. Il WR atteso è ~52–54%.
- **Il filone "segnale con eccesso misurabile" resta praticamente esaurito** sulle fonti già in database. Dopo 20 query la letteratura aperta non fornisce un secondo segnale con eccesso dimostrato.
- **Conclusione provvisoria.** Con i dati attuali, il problema potrebbe stare nel conto da 50k più che nelle strategie. Non lo dico come risultato definitivo, perché la ricerca di questa sessione è stata minima.

## Scartate da me

| Idea | Fonte | Motivo |
|---|---|---|
| Benchmark TWAP/VWAP come pressione di prezzo | [arXiv 1803.08336](https://arxiv.org/abs/1803.08336) | Modello teorico: nessuna regola, nessun test, nessun costo |
| DriftPullback su YM | report `DPB_S2_IS_PORT-YM` | Già misurata: t = 0,2 |

## Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Ci torno? |
|---|---|---|
| arXiv 1803.08336 | Teoria senza regole | No |
| arXiv 1005.3535 | Non aperta | Bassa priorità: cross-section azionario |
| Fonti DA LEGGERE su MOC, VWAP, M2K | Non aperte per mancanza di tempo | Sì, ma sono pagine di vendor e forum, con valore basso |

```json
{
  "candidates": [],
  "sources_reviewed": [
    {
      "url": "https://arxiv.org/abs/1803.08336",
      "title": "Equilibrium Effects of Intraday Order-Splitting Benchmarks (Choi, Larsen, Seppi)",
      "kind": "paper",
      "verdict": "scartato",
      "reason": "Modello teorico di TWAP/VWAP: nessuna regola codificabile, nessun test su dati, nessun costo",
      "candidate": null
    }
  ]
}
```

---

## Gate 0 — verifica automatica (gate0.py, nessun modello)

Ricalcolato da codice, non dal ricercatore. `?` = numero non fornito.

| Candidata | Esito | Controlli |
|---|---|---|
