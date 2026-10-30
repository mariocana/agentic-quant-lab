# VaultBreak — istruzioni Stage 1

Codice: `VaultBreak.txt` (signal) + `VaultBreak_Levels_Ind.txt` (indicatore, disegna NoiseUp e VWAP).

## Chart
- **@NQ · 5 min · sessione RTH** (Format Instrument → Settings → session template
  "CME RTH" / 08:30–15:00 CT), timezone **Exchange**. Su un chart 24h il codice non
  funziona (il reset di sessione avverrebbe a mezzanotte).
- Lead‑in: con `DailyATRLen 252` servono **252 sessioni prima** del periodo che vuoi
  valutare (≈ 1 anno): per i primi 100 giorni di test usare `DailyATRLen 20` così parte
  subito, poi rimettere 252 per lo Stage 2.
- Max bars back 100; costi $2.50/lato + 1 tick.

## Verifica meccanica (Gate 1)
Nella List of Trades e sul chart:
- ingresso all'**apertura della barra successiva** a una chiusura sopra NoiseUp **e** sopra
  VWAP, mai prima delle 08:45 né dopo le 14:00;
- stop = 100 pt sotto l'ingresso, target = 50 pt sopra (con 1 contratto: −$2.000 / +$1.000);
  con `Num_Contracts 10` gli importi ×10 (lo stop built‑in è per posizione: il codice lo
  scala con `CurrentContracts`);
- uscita `VB-VWAPX` dopo 2 chiusure consecutive sotto il VWAP; `VB-TIMEX` alla barra
  ≥ 14:50; nessuna posizione overnight;
- max 3 ingressi al giorno, re‑entry ammesso dopo un'uscita.

## Differenze rispetto al template del corso
- ATR **rolling 252** (template `10.`), non quello "seeded/expanding" (template `5.`):
  i risultati non sono confrontabili con la scheda VaultBreak_NQ_.pdf, va validato da capo.
- Orari convertiti ET → CT (0845 / 1400 / 1450).
- Stop/target in **punti** anziché in $ fissi, così scalano da soli con i contratti.
- `Volume` con fallback su `Ticks` se il feed non porta il volume.
