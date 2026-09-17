# SPEC — Gold Asian Range Breakout (Stage 0)

**Ipotesi**: durante la sessione asiatica l'oro forma un range compresso; all'arrivo
della liquidità di Londra/USA la rottura di quel range tende a proseguire fino a metà
mattina USA.
**Perché**: gli ordini vengono piazzati **nell'istante** in cui il range chiude, senza
gap fra livello e ordine (è ciò che uccide i breakout "del giorno prima"); il flusso
europeo/USA è più grande di quello asiatico e ne rompe l'equilibrio. Chi perde: chi
vende il range ai suoi estremi. Vincitore Strategy of the Month lug/ago 2026 (live: PF
1.64 poi 3.28); ricerca: Sharpe 0.89, PF 1.18, WR ~34%.
Ruolo nel basket: **altro asset** (agosto 2026 NQ piatto, oro no) e altro orario.

| | |
|---|---|
| Famiglia | trend / range breakout |
| Strumento · TF · sessione | @GC (sviluppo) → MGC · 15 min · Globex, chart CT |
| Range | 21:00–01:00 NY = **20:00–00:00 CT** (attraversa la mezzanotte: il codice del corso gestisce il wrap) |
| Entry | buy stop al range high, sell stop al range low, OCO, alla chiusura del range |
| Stop | 1.0 × ampiezza del range |
| Target | nessuno (variante A) |
| Time exit | 11:00 NY = **10:00 CT** |
| Trade/giorno | 1 |
| Profilo prop | **variante A non lo rispetta** (WR 34%, R:R > 1): candidata solo come diversificatore funded a size piccola. **Variante B** (pre‑registrata): TP = 1R (poi 0.5R) per il profilo eval. |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Varianti pre‑registrate (Stage 4)**: B = TP 1R / 0.5R; StopFrac 0.5/0.75; long only;
finestra range 22:00–01:00 CT.
**Note**: GC = $100/pt (tick 0.10 = $10), MGC = $10/pt. Range tipico $10–25 → rischio
$1.000–2.500 per GC, $100–250 per MGC. Nel report del corso il chart era in ora NY con
day boundary 17:00: verificare che con il chart CT le finestre coincidano.
**Kill**: gate pipeline. La variante A entra in pipeline solo per lo Stage 8 (basket),
non per l'eval.
