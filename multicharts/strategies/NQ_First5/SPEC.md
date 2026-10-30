# SPEC — NQ First5 (Stage 0)

**Ipotesi**: la direzione dei primi 5 minuti della sessione cash NY persiste fino alla
chiusura; si entra in quella direzione e si tiene tutta la seduta.
**Perché**: all'apertura entrano in blocco gli ordini istituzionali accumulati fuori
sessione (MOO, ribilanciamenti, esecuzioni programmate); quel flusso imprime il drift
della giornata. Chi perde: chi fade l'apertura e chi entra tardi. Fonte: template del
corso (18), dichiarato **non validato** dall'autore per il Bridge → per noi è un
candidato da validare, non un risultato.
**Ruolo nel basket**: è **l'unica candidata con un lato short reale** (ORB e VaultBreak
sono long‑only). Matteo: per le eval è rilevante avere anche short, non solo long.

| | |
|---|---|
| Famiglia | momentum / drift intraday, long e short |
| Strumento · TF · sessione | @NQ · **5 min** (obbligatorio) · Globex 24h, chart CT |
| Barra di riferimento | quella che chiude a **08:35 CT** (prima barra della sessione NY) |
| Entry | close > EMA(12) → long; close < EMA(12) → short; *this bar at close* |
| Exit | prima barra con Time ≥ **15:00 CT**, a chiusura; `SetExitOnClose` come backstop |
| Stop / target | **nessuno** nella versione validata |
| Trade/giorno | 1 |
| Filtri (UseFilters 1) | range barra rif. ≥ 0.15 × ADR(20); ADR(20) ≥ 1.10 × ADR(100) — misurati in range medio di sessione, non in punti |
| Profilo prop | da misurare: R:R non definito (nessun TP/SL). **Senza stop non è deployabile**: vedi sotto. |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
Il base case (`UseFilters 0`) è il benchmark: la versione filtrata deve batterlo
sull'avg trade in **entrambe** le metà dell'IS, altrimenti resta il base.

**Varianti pre‑registrate (Stage 4)**
1. `StopPts` > 0 — **obbligatoria per l'uso prop**. Senza stop una seduta estrema (NQ
   −1.000 pt) vale ~$2.000 su 1 MNQ, cioè l'intero drawdown Apex in un giorno. Da
   calibrare come frazione dell'ADR e validare con lo split‑sample: se lo stop distrugge
   l'edge, la strategia non è utilizzabile per la prop (kill).
2. `UseFilters 1` con `VolRegimeRatio` 1.0 / 1.10 / 1.20.
3. Solo short (`AllowLongs 0`): il lato short è quello che manca al basket; va misurato
   anche da solo.
4. `EMALength` 8 / 12 / 20 (cluster, non picco).

**Kill**: gate della pipeline. In più, kill specifico se con lo stop obbligatorio
l'avg trade netto scende sotto $70 o il WR sotto il 50%.

**Attenzione — correlazione**: stesso strumento, stessa ora e stessa idea di drift
dell'ORB. Misurare la correlazione con ORB già dopo lo Stage 2, senza aspettare il
gate 8: se è alta, nel basket ne entra una sola (o si tiene First5 solo per lo short).

## Aggiunte al codice prima dello Stage 1 (01/10/2026)

Non sono logica di trading, sono prerequisiti della pipeline che al codice mancavano:

- **`ShowLog`** (default `false`) → due righe di log: `F5 EOD` a fine sessione con `rN`,
  ADR breve, ADR lungo e il loro rapporto; `F5 SIG` sulla barra delle 08:35 con close, EMA,
  direzione, range della barra di riferimento ed esito dei due filtri. Senza, lo Stage 1
  non è verificabile.
- **`TradeStartEL` / `TradeEndEL`** (default 0 = spenti) → separano il warm-up di 100
  sessioni (`VolRegimeLongLen`) dal periodo valutato. Agiscono **solo sugli ingressi**: una
  posizione aperta resta gestita. Stesso schema già validato su VaultBreak.

Checklist operativa: `CHECKLIST_Stage1.md`.

## Budget di rischio noto in anticipo (da ORB e VaultBreak)

Le due strategie chiuse sono uscite dal Gate 3 a **$3.121** e **$3.109** di drawdown per
micro al 95° percentile Monte Carlo, contro un MLL di **$2.000**. Due logiche indipendenti,
scarto dello 0,4%: è la misura di quanto costa tenere 1 micro NQ in un sistema intraday
direzionale con stop da ~$200/micro.

**Conseguenza per First5**: il budget è `95° percentile ≤ $2.000 per micro`, che con i
fattori di amplificazione misurati (1,67× su VaultBreak, 2,56× sull'ORB) significa puntare a
un **drawdown storico di $10.000–12.000 con 1 mini**. Va deciso allo Stage 0 della variante
`StopPts`, non scoperto al Gate 3 — è esattamente l'errore che abbiamo già pagato due volte.

---

# Stage 2 — IS 2020‑2024: **Gate 2 fallito**

Sei run, 08/10/2026. Chart @NQ 5 min Globex 24h CT, dati dal 01/01/2019 (warm‑up) al
31/12/2024, costi `7.5$ per Contract` + slippage 0, 1 contratto, `StopPts 0`.
Periodo valutato con il gate date: `1200101` → `1241231`.
Report in `reports/`.

| run | trade | net | avg trade | WR | PF | DD close‑to‑close | peggior trade |
|---|---|---|---|---|---|---|---|
| **1 — IS base** | 1.291 | 112.095 | $86,83 | 51,4% | 1,076 | −87.975 | −$10.845 |
| **2 — IS filtrata** | 294 | 107.780 | **$366,60** | 53,1% | 1,275 | −50.045 | −$10.445 |
| 3 — 1ª metà base | 645 | 26.220 | $40,65 | 51,5% | 1,034 | −78.770 | — |
| 4 — 1ª metà filtrata | 177 | 61.450 | **$347,18** | 53,1% | 1,241 | −50.045 | — |
| 5 — 2ª metà base | 646 | 85.875 | $132,93 | 51,4% | 1,121 | −55.295 | — |
| 6 — 2ª metà filtrata | 117 | 46.330 | **$395,98** | 53,0% | 1,341 | −19.910 | — |

## I filtri funzionano, e questo era pre‑registrato

La regola scritta allo Stage 0 era: la filtrata entra **solo se batte il base sull'avg trade
in entrambe le metà**. Lo fa, e non di poco — **$347 contro $41** nella prima metà, **$396
contro $133** nella seconda. Il filtro di regime taglia il 77% dei trade e quasi raddoppia
il profit factor. **La versione filtrata diventa la candidata.**

Vale la pena notare *come* lo fa: non alzando il win rate (51,4% → 53,1%, quasi nulla) ma
scegliendo giornate con escursione più ampia. L'avg win passa da $2.387 a $3.199.

## Ma il Gate 2 non passa, e non passa per il motivo di sempre

Giudicato sulla candidata (run 2):

| metrica | soglia | ottenuto | |
|---|---|---|---|
| n. trade | ≥ 200 | 294 | ✔ |
| avg trade netto | ≥ $70 | $366,60 | ✔ |
| profit factor | ≥ 1.2 | 1,275 | ✔ |
| win rate | ≥ 55% | 53,1% | ✘ |
| **max DD ÷ 10** | **≤ $1.000** | **$5.784** | ✘ **5,8×** |
| **peggior trade ÷ 10** | **≤ $500** | **$1.044** | ✘ **2,1×** |
| tabella annuale | nessun anno > 50% | 2020 = 64,9% | ✘ |
| segno stabile | — | 2021 = **−32,7%** | ✘ |

Il base case va peggio su tutto tranne il numero di trade: PF 1,076, DD per micro $8.950.

Lo Stage 0 aveva già scritto il bersaglio: *«puntare a un drawdown storico di $10.000–12.000
con 1 mini»*. Siamo a **$50.045**. Non è un margine, è un ordine di grandezza.

## La variante `StopPts` non può salvarla — calcolato prima di spendere un run

`StopPts` era pre‑registrata allo Stage 0 come **obbligatoria per l'uso prop**, quindi
provarla non sarebbe un ripescaggio post‑hoc. Prima di lanciarla ho però ricostruito dalla
lista trade un **limite massimo ottimistico**: ogni perdita tagliata allo stop, e **nessun
vincente toccato** dallo stop intrabar. La realtà sta sotto questa riga, mai sopra.

| stop (pt) | net | avg | PF | DD ÷ 10 | trade tagliati |
|---|---|---|---|---|---|
| nessuno | 107.780 | $367 | 1,275 | **$5.004** | — |
| 300 | 134.130 | $456 | 1,367 | **$4.614** | 12 |
| 200 | 174.835 | $595 | 1,539 | **$3.430** | 35 |
| 150 | 218.325 | $743 | 1,778 | **$2.527** | 52 |
| **100** | 280.200 | $953 | 2,280 | **$1.342** | 71 |

Anche con uno stop da **100 punti** — stretto al punto da essere rumore su uno strumento il
cui ADR di sessione sta fra 300 e 600 punti — il limite *ottimistico* resta sopra la soglia
di $1.000. E il valore vero sarebbe peggiore, perché uno stop così stretto trasformerebbe in
perdite un buon numero dei vincenti che qui ho lasciato intatti.

Il vincolo che non si sposta: **avg loss $2.836, cioè $284 per micro**. Tenere una posizione
per l'intera sessione su NQ senza stop costa questo, e il filtro di regime — che seleziona
apposta le giornate più ampie — lo **aumenta**, non lo riduce.

## Verdetto

**Gate 2 fallito.** Il Monte Carlo dello Stage 3 non si lancia: gira su un report che già
sfonda di 5,8× la soglia di drawdown, e il 95° percentile è per costruzione peggiore del
drawdown storico.

L'edge esiste — $366 di avg trade netto su 294 trade con PF 1,275 non è rumore. Non entra
nel conto. È la **terza volta di fila**, con la stessa causa:

| strategia | drawdown per micro | dove è morta |
|---|---|---|
| ORB Breakout | $3.121 (95° pct MC) | Gate 3 |
| VaultBreak | $3.109 (95° pct MC) | Gate 3 |
| **NQ First5** | **$5.004 (storico)** | **Gate 2** |

Tre logiche indipendenti sullo stesso strumento, tutte con un edge misurabile, tutte fuori
budget per la stessa ragione. Vedi la domanda aperta sul Gate 3 in `pipeline_prop.md`: il
trigger che avevo fissato parlava del Gate 3, ma la causa è la stessa e ora i casi sono tre.

---

# Chiusa — cimitero, causa di morte **B** (08/10/2026)

**Decisione presa dopo il Gate 2 fallito.** Causa **B — non entra nel conto**: l'edge c'è,
l'unità di rischio è troppo grande per un MLL da $2.000.

Non è causa A. La versione filtrata fa **$366,60 di avg trade netto su 294 trade** con
PF 1,275, i filtri battono il base case in **entrambe** le metà dell'IS come richiesto dalla
regola pre‑registrata, e il profitto è positivo in tre anni su cinque. È una strategia che
guadagna; non è una strategia che si può dimensionare su questo conto.

**Il numero che la chiude**: drawdown $5.004 per micro contro $1.000 di soglia, e avg loss
$2.836 (**$284 per micro**). La variante `StopPts`, pre‑registrata allo Stage 0 come
obbligatoria, è stata verificata per calcolo prima di spendere un run e **non basta**:
neppure a 100 punti il limite ottimistico scende sotto soglia.

**Cosa la riaprirebbe** (regola del cimitero — si ri‑testa in minuti, non si ricostruisce):

- un conto con **MLL molto più alto** rispetto al target, tale da assorbire $284 per micro
  di perdita media;
- lo **stesso schema su uno strumento meno volatile per tick** — MES invece di MNQ è il
  candidato naturale, ma attenzione: il porting ES di VaultBreak è stato bocciato perché
  l'edge in R si indeboliva del 26%, quindi va misurato, non assunto;
- una **riscrittura dell'uscita**, non dello stop: il costo sta nel tenere la posizione per
  l'intera sessione. Un'uscita a tempo più corta o a obiettivo sarebbe un'altra strategia,
  cioè una **nuova Stage 0**, non una riapertura di questa.

**Resta il lato short.** First5 era l'unica candidata con uno short reale, e questo non è
cambiato: il basket ne ha ancora bisogno. Il lato short ha fatto **$30.125 su 53 trade** nel
run del gate date e nel base IS è il lato migliore — informazione da portare alla prossima
strategia long‑short, non da usare per riaprire questa.

Report completi in `reports/` — Stage 1 (sette file) e Stage 2 (sei file).
