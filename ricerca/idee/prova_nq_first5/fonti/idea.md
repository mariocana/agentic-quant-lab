> Idea di Mario, come l'aveva scritta prima di qualsiasi misura. La regola da misurare e' il caso base, senza filtri e senza stop.

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

