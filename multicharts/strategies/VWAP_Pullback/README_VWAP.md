# VWAP Pullback — istruzioni Stage 1

Codice: `VWAP_Pullback.txt` (signal). Indicatore di supporto: il VWAP di sessione
(`mc/protocollo/6. Code Templates/...` oppure `VaultBreak_Levels_Ind` che plotta anche il VWAP)
e l'ORB Box del corso, per vedere range e livello.

## Chart
- **@NQ · 1 min · sessione Globex 24h** (17:00–16:00 CT), timezone **Exchange**,
  volume da trade data. Il reset giornaliero è alle 23:00 CT (mezzanotte NY): serve la
  sessione piena, non RTH.
- Max bars back **≥ 42** (`2 × StopSwingLen + 2`). Costi $2.50/lato + 1 tick.
- Ultimi ~100 giorni per la verifica meccanica.

## Verifica meccanica (Gate 1)
- L'opening range si forma fra 08:30 e 09:00 CT; il bias si attiva alla prima **chiusura**
  oltre il range e resta latchato.
- L'ingresso arriva **solo dopo** un ritorno sul VWAP: con `RetestMode 1` il minimo (long)
  deve aver toccato il VWAP, poi serve una chiusura sopra; con `RetestMode 2` serve prima
  una chiusura sotto e poi il reclaim.
- Stop al pivot (`StopMode 1`) o all'estremo del pullback (`StopMode 2`); target al pivot
  opposto. Nel log (`ShowLog 1`) trovi stop, target e RR di ogni trade.
- **Un trade al giorno**, nessuna posizione dopo le 14:55 (`UseEODFlat 1`), niente overnight.
- Con `Num_Contracts 10` il P&L per trade deve essere ×10.

Attenzione al numero di trade: la combinazione bias + retest + validità dei pivot è
selettiva; se escono pochissimi trade, prima di toccare la logica controlla che il VWAP
sia valido (finestra 08:30–15:00) e che i pivot si formino (StopSwingLen non troppo alto).

## Differenze dal template del corso
- Rimosso tutto il sizing per rischio %/margine: **1 contratto**, la size in micro la
  decide il simulatore prop.
- **EOD flat obbligatorio** (l'originale teneva overnight fino alla risoluzione del bracket):
  non ammesso per la prop.
- Flag 0/1 per l'ottimizzatore; orari già in CT.
- `Volume` con fallback su `Ticks`.

## Varianti pre‑registrate (Stage 4, non ora)
`RetestMode` 1 vs 2 · `StopMode` 1 vs 2 · `MinRR 1` · TP fisso in R al posto del pivot ·
gate ADX(14) > 20/25 sul 5 min (da ricostruire, non verificato) · long only.
