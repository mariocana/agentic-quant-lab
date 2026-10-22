<!-- researcher.py, 20/10/2026, model claude-sonnet-5-5, effort medium, TEST -->

# Ricerca del 20/10/2026: nessuna candidata consegnata

**Esito: zero candidate e zero quasi-candidate.** La ricerca web si è interrotta subito. Ho lanciato quattro query. La prima ha restituito un solo risultato leggibile, già nel database tra le scartate. Le altre tre sono state bloccate da "Server tool use limit exceeded". Non ho letto nessuna fonte nuova e non ho nessun dato nuovo da portare. Preferisco consegnare un risultato vuoto che costruire candidate a tavolino, come chiede il prompt: ogni numero senza fonte sarebbe [manca].

## Tabella di sintesi

| # | Nome | Strumento · TF | Famiglia | Stop (punti → $/micro) | n/anno | WR | R:R | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| – | nessuna | – | – | [manca] | [manca] | [manca] | [manca] | – | – |

## Cosa posso dire usando solo i documenti che mi hai dato

**1. "DriftPullback su @YM" (ricerca_18-10, punto 3) è già stato provato.**
- Nella tabella REPORT MISURATI c'è `DPB_S2_IS_PORT-YM_2020-2024`: n 3.393, t 0,2, WR 61,8%, R:R 0,62, avg $1,54.
- Il porting su YM non ha edge sull'IS. Non è una candidata e non va riproposta.
- Sono fuori anche le varianti su MYM e M2K con la stessa logica. Il database le dà come scartate: servirebbe misurare k prima.

**2. LastHalfHour è già in pipeline (Stage 0), senza report misurati.**
- È la fonte con il miglior filtro compilato: testata su futures, replicata, con flusso forzato e t di 4–8.
- I costi nel paper non sono considerati, e Gao et al. nel database sono stimati a ~2,2× il costo.
- Non la riporto come nuova.

**3. Evento macro delle 08:30 CT.**
- Viene citato come "cosa resta da provare", ma sta a 2–3 eventi a settimana. Questo viola il vincolo di frequenza di ≥ 2 trade al giorno.
- Il database scarta già le fonti correlate: Kurov et al., Hu-Pan-Wang-Zhu, Bernile-Hu-Tang.

**4. Osservazione sul processo, separata dai criteri.**
- Il prompt (vecchio) chiede ancora di cercare "mean reversion intraday" e "WR ≥ 55% con R:R 0,5–1".
- ricerca_18-10 e Zarattini-Pagani dicono che il profilo lo impone il bracket e che la mean reversion corta autonoma non paga.
- Ho seguito il più recente: cercare segnali con un eccesso misurabile, di qualunque forma.
- Non propongo di cambiare i gate.

## Filoni ancora aperti (non esauriti, solo non raggiunti)

Queste sono le query che avevo previsto e che non sono state eseguite:
- Impatto degli squilibri MOC delle 15:50 ET sugli indici. Probabilmente richiede dati di book, quindi forse è già escluso.
- Opening range reversal / reversion su M2K.
- Pattern orari legati al VWAP come benchmark di esecuzione. Ricadrebbe probabilmente su Heston-Korajczyk-Sadka, già cercato.
- Pullback con target piccolo su MYM.

Vale la pena rilanciarle in una sessione nuova, con il limite di ricerca ripristinato.

## Scartate da me

| Idea | Fonte | Motivo |
|---|---|---|
| DriftPullback su YM | report DPB_S2_IS_PORT-YM | t 0,2 su 3.393 trade: nessun edge |
| Order-flow imbalance E-mini e notizie macro | https://arxiv.org/html/2508.06788 | già scartata: richiede dati di book al secondo |

## Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| "MOC imbalance announcement 15:50 index futures price impact intraday" | solo arXiv 2508.06788, già scartato | sì, query da rifare ma con parole diverse |
| Altre tre query (M2K opening range, VWAP end-of-hour, pullback MYM) | nessun risultato: limite strumento superato | sì, mai eseguite |

```json
{
  "candidates": [],
  "sources_reviewed": [
    {
      "url": "https://arxiv.org/html/2508.06788",
      "title": "Returns and Order Flow Imbalances: Intraday Dynamics and Macroeconomic News Effects",
      "kind": "paper",
      "verdict": "scartato",
      "reason": "Già scartata: richiede order flow BBO al secondo, dati che non abbiamo. Riaffiorata nella query MOC.",
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
