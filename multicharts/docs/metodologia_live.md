# Metodologia live (soldi propri) — IN STAND-BY

**Stato:** congelata il 15/10/2026. **Da riesumare quando:** i payout iniziano e il conto si
forma. Fino a quel momento **non si applica a nessuna candidata**.

**Bozza della pipeline (12/11/2026):** [pipeline_live.md](pipeline_live.md), dalla SPEC al live,
con il conto minimo a $100.000. Non in vigore: i criteri qui sotto restano la fonte finche' Mario
non la conferma.

**Perche esiste questo file:** il corso separa i due mondi in modo esplicito e noi li avevamo
mescolati. Vedi [prop_vs_live.md](prop_vs_live.md). Questi criteri non sono sbagliati: sono
**fuori tempo**. Applicati a una eval uccidono candidate che la eval accetterebbe.

> *"This is extremely important when you're trading with **your own capital** rather than when
> you're trading with prop firms."* — Live 001, 823

## I criteri tolti da Gate 2 il 15/10/2026

| criterio | valore | perche e live e non prop |
|---|---|---|
| **PF ≥ 1,2** | lordo, sull'IS | Live 002, 273: *"your biggest enemy is the trailing drawdown and **not the profit factor**"*. Con WR alto e R:R basso il PF resta vicino a 1 per costruzione: e la stessa informazione di WR e R:R, contata una seconda volta |
| **avg trade ≥ $70 (NQ)** | $7/micro | Live 002, 245: l'esempio deployato ha avg netto **$77** e il corso commenta *"it's not huge, the edge here is not in a single trade, is in consistency and repetition"*. E un numero da **guardare** (Live 003, 23), non una soglia |
| **nessun anno > 50% del profitto** | su 5 anni | guarda la tenuta su un orizzonte piu lungo della eval. Una eval dura settimane |

## I criteri tolti da Stage 5 (OOS)

| criterio | valore |
|---|---|
| **avg trade ≥ $70** | stessa ragione di sopra |

## Criteri che restano solo qui (mai stati in pipeline, si aggiungono alla ripresa)

- **robustezza al cambio di regime**, e la ragione **strutturale** per cui l'edge dovrebbe
  continuare a esistere — e il contesto esatto della frase di Live 001, 823
- **drawdown su 5 anni** come vincolo di capitale proprio, non come proxy dell'MLL
- monitoraggio del regime in esercizio

## Cosa NON spostare qui

Restano prop, non toccarli: **t** (il corso lo cita, Live 002: t = 2,229 OOS), **n**,
**time range**, **win rate**, **R:R**, **pass rate**, **trailing drawdown dentro la
simulazione**, **contratti come output**.
