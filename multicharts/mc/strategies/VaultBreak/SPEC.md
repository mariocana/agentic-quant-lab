# SPEC — VaultBreak NQ (Stage 0)

**Ipotesi**: quando NQ, in RTH, chiude sopra una "noise boundary" = open di sessione +
0.6 × range giornaliero medio, e sta sopra il VWAP di sessione, il movimento è
direzionale e non rumore; conviene comprarlo e tenerlo finché il VWAP regge.
**Perché**: il range medio giornaliero definisce quanto il prezzo si muove "per caso"
(Larry Williams / Zarattini noise band); superarlo con il VWAP a favore segnala flusso
istituzionale netto in acquisto. Chi perde: chi vende il breakout come esaurimento.
Nel corso: WR ~70% negli ultimi 40 giorni, usato nel basket delle live (pass rate
singola 43%).

| | |
|---|---|
| Famiglia | trend / volatility breakout |
| Strumento · TF · sessione | @NQ · 5 min · **RTH** (08:30–15:00 CT) |
| Noise boundary | `SessOpen + NoiseMult(0.6) × DailyATR`, DailyATR = media **rolling 252 sessioni** del range (versione `10. long rolling ATR`: indipendente dalla data di partenza) |
| Entry | close > NoiseUp **e** close > VWAP di sessione, 08:45–14:00 CT, long only |
| Stop | $2.000 per contratto NQ (100 pt) — `SetStopLoss`, scala con i contratti |
| Target | $1.000 per contratto (50 pt) — R:R nominale 0.5 |
| Altre uscite | 2 chiusure consecutive sotto il VWAP; flat 14:50 CT |
| Trade/giorno | max 3 |
| Profilo prop | R:R 0.5, WR alto → ok (l'uscita VWAP chiude la maggior parte dei trade prima di TP/SL) |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: NoiseMult 0.5/0.7 con DailyATRLen 252/504
(ri‑ottimizzare insieme, cluster); MaxTradesPerDay 1 vs 3; TP/SL in punti anziché $.
**Note codice**: template del corso ha gli orari in ET (0945/1500/1550) → su chart CT
usare 0845/1400/1450. `SetStopLoss`/`SetProfitTarget` sono per posizione: con N
contratti moltiplicare. Il DailyATR seeded/expanding del template originale NON si usa.
**Kill**: gate pipeline. Se in OOS il WR scende sotto 55% con R:R 0.5, la strategia non
serve alla prop.
