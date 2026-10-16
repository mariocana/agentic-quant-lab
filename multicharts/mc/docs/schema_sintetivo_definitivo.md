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

---

# Session template e timezone: uno per strategia

**Non c'e una risposta sola.** Lo decide il codice, ed e scritto nell'header di ogni file.
L'unico invariante e il **timezone: sempre Exchange (CT)**.

| strategia | template obbligatorio | perche |
|---|---|---|
| **DriftPullback** | **Globex 24h** (17:00-16:00 CT) | il drift e la MA sui 15m servono le barre pre-apertura |
| **VaultBreak** | **solo RTH** (08:30-15:00 CT) | il reset usa `Date <> Date[1]`: su un chart 24h il «session open» sarebbe la **mezzanotte** |
| **Gold Asian Range** | **24/7** | il range asiatico 20:00->00:00 scavalca la mezzanotte |

**Gli orari negli input sono in ORA DEL CHART.** Con un chart ET sono sbagliati di un'ora e
non te lo dice nessuno: il backtest gira e da numeri plausibili e falsi.

## Come si verifica dal report

Il foglio Settings di MultiCharts **non registra il session template**. Si deduce dall'**ora
dell'ultima barra**, e solo se il grafico finisce su un giorno completo:

| ultima barra | template |
|---|---|
| **16:00 CT** | Globex 24h |
| **15:00 CT** | RTH |
| altro | giorno incompleto: non si deduce, va guardato il grafico |

`check_report.py` lo stampa fra i controlli preliminari.

**Verificato sugli IS**: DriftPullback chiude alle 16:00 (Globex, corretto), VaultBreak alle
15:00 (RTH, corretto). **Sugli OOS no**: i loro grafici finiscono a oggi a meta sessione.

---

# Far girare lo script del CORSO (Colab), e confrontarlo col nostro

## Dove sta

`education/protocollo/4. Validation, Risk & Going Live./3. Colab_PropFirm_Montecarlo.txt`
contiene il link. Il notebook si chiama **`PropFirm_MonteCarlo_Apex50K_funded_IP.ipynb`** —
«Prop Firm Challenge — Monte Carlo Pass Rate Estimator».

C'e anche il secondo, `2. Colab_Montecarlo.txt`, che e il Monte Carlo generico sulla strategia
(non sul passaggio della eval). Sono i «two colab files» di Live 003.

Si apre **senza login** in sola lettura. Per eseguirlo serve un account Google e
**File -> Salva una copia in Drive**: finche non lo copi, non puoi far girare le celle.

## Cosa ti occorre

**1. Il CSV, con i nomi di colonna suoi.** Il notebook pretende `trade_id`, `contracts`,
`profit_usd`, `direction` e una data. Il foglio di MultiCharts ha gli stessi dati con nomi
diversi, e sta nel **terzo** foglio: `pd.read_excel` da solo leggerebbe il primo, che e il
sommario. Convertitore:

```bash
python3 mc/docs/to_colab_csv.py mc/strategies/NOME/reports/NOME_S5_OOS.xlsx
```

Scrive `NOME_S5_OOS_colab.csv` accanto all'originale, una riga per trade. Controlla che il
conteggio, il WR e l'avg stampati combacino con `check_report.py`: se non combaciano, non
caricare niente.

**2. Cambiare i parametri, perche il notebook e per APEX e noi siamo su LucidFlex.**

| | Apex 50K (default del notebook) | **LucidFlex 50k (il nostro)** |
|---|---|---|
| target | $3.000 | $3.000 — uguale |
| max drawdown | **$2.500** EOD trailing | **$2.000** |
| scadenza | **21 giorni** di trading | **nessuna** |
| lock del trailing | a +$100 dal saldo iniziale | a **$50.100** |

Se non li cambi, la risposta e sul conto sbagliato.

**3. Azzerare i costi, altrimenti li conta due volte.** In CELL 2 ci sono
`COMMISSION_PER_CONTRACT = 2.25` e `SLIPPAGE_PER_CONTRACT = 5.0`. Il nostro export ha gia i
costi dentro ($7,50/contratto/lato), quindi vanno messi **entrambi a 0**.

In alternativa `python3 mc/docs/to_colab_csv.py report.xlsx --lordo` riporta il P&L al lordo
togliendo $7,50/lato, e allora i costi li metti nel notebook.

**4. Sistemare il sizing.** `NUM_CONTRACTS = 1.7` e in **contratti NQ equivalenti**: 1 micro
= 0,1. Due micro si scrivono `0.2`. Stessa cosa in `SWEEP_CONTRACTS`. E `RISK_PER_CONTRACT`
va messo al nostro R per contratto NQ intero.

## Cosa ha il suo che il nostro non ha

Gli **scenari di degrado**: rigira la simulazione con WR −3/−5/−8 punti e P&L ridotto del
10/15/25/30%. E la domanda «e se dal vivo rende meno del backtest», che il nostro non pone.
Vale da sola il giro.

## Cosa ha il nostro che il suo non ha

- il controllo dello **stato attuale della curva** (quanto siamo lontani dal massimo);
- il **breach dentro il trade** e non solo alla chiusura;
- il guardrail sulle **finestre indipendenti**, che dichiara inaffidabile un numero invece di
  stamparlo.

## Il confronto da fare

Girare i due sulla **stessa** lista di trade e sugli **stessi** parametri di conto. Se danno
pass rate vicini, il nostro e validato. Se divergono, il primo sospetto sono i costi contati
due volte e il secondo la scadenza a 21 giorni lasciata accesa.

Il nostro, su DriftPullback OOS a 2 micro: **42,3% per tentativo, 89% entro quattro**.
