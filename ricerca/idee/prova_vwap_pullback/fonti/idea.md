> Idea di Mario, come l'aveva scritta prima di qualsiasi misura.

# SPEC — VWAP Pullback NQ (Stage 0)

**Ipotesi**: dopo che NQ ha rotto il range 08:30–09:00 CT (bias della sessione), il
primo ritorno sul VWAP di sessione e la ripresa nella direzione del bias è un ingresso
a prezzo migliore del breakout, con stop stretto e target al pivot precedente.
**Perché**: il 90%+ del flusso istituzionale è eseguito da algo benchmarked al VWAP;
il VWAP è la zona dove il flusso passivo si attiva e il prezzo reagisce. Chi perde: i
chaser che comprano il breakout e i fader del primo pullback. Nel corso: avg ~$80, PF
1.2, WR 58% (NQ 1 min dal 2021); variante con gate ADX (Agnello): WR 82%, avg $300 OOS
— **non verificata**, il codice ADX non è nel materiale, va ricostruita.
Ruolo nel basket: la componente "mean reverting" (compra il ritorno al VWAP) con
correlazione ~0 rispetto a ORB/VaultBreak.

| | |
|---|---|
| Famiglia | mean reverting a livello micro, continuation a livello di sessione |
| Strumento · TF · sessione | @NQ · **1 min** · Globex 24h, chart CT, MaxBarsBack ≥ 42 |
| Bias | close fuori dal range 08:30–09:00 CT (latched) |
| Entry | retest del VWAP di sessione (touch, o close‑through + reclaim) → a mercato sulla chiusura del reclaim, nella direzione del bias, 09:00–14:00 CT |
| Stop | pivot swing (StopSwingLen 20) o estremo del pullback (StopMode 2) |
| Target | ultimo pivot confermato (TargetSwingLen 5) |
| Time exit | **flat 14:55 CT obbligatorio** (`UseEODFlat true` — l'originale tiene overnight: non ammesso per la prop) |
| Trade/giorno | 1 |
| Profilo prop | da verificare: R:R variabile (pivot); se < 55% WR → Stage 4 con TP fisso 0.5–1R |

**IS**: 2021‑01‑01 → 2024‑12‑31 (dati 1 min) · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: gate ADX(14) > 20/25 sul 5 min; StopMode 1 vs 2;
MinRR 1; TP fisso in R al posto del pivot; long only.
**Note codice**: template `13. VWAP Pullback NQ Margin Vol 1min TF.txt` — usare
`UseVolSizing false`, `PositionSize 1`, `UseEODFlat true`. Volume da trade data.
**Kill**: gate pipeline; se con EOD flat l'avg trade scende sotto $70, non sopravvive ai costi.

---

