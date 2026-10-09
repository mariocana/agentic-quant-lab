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

---

# Stage 1 — **Gate 1 passato** (09/10/2026)

Dettaglio e prove in `CHECKLIST_Stage1.md`, report in `reports/`. Qui solo ciò che
**modifica la spec**. Il corpo sopra resta com'era scritto prima dei run: è la
pre-registrazione e non si riscrive.

### Risolto: la finestra del range con chart CT

La domanda aperta («nel report del corso il chart era in ora NY con day boundary 17:00:
verificare che con il chart CT le finestre coincidano») è chiusa. Il log `GAR RNG` dà
`barre= 16` e `armTime= 0` su tutte le 83 giornate = 20:00 → 00:00 esatte. MC timbra la
barra di mezzanotte `0`, non `2400`, quindi il wrap `Time >= 2000 or Time < 0` chiude la
finestra al punto giusto.

### Corretto: sessione del chart

Il template `COMEX: Metals Futures (Electronic)` **non va usato**: lascia il chart senza
barre fra 07:45 e 14:15 e manda il time exit sulle 14:15. Serve un template **24/7**.

### Corretto: ampiezza del range, quindi rischio per trade

| | spec (assunto) | misurato |
|---|---|---|
| range | $10–25 | **mediana 37,8 pt**, media ≈ 42 pt |
| rischio per GC | $1.000–2.500 | **$3.780** mediano |
| rischio per MGC | $100–250 | **$378** mediano, **$442** nel caso peggiore del campione |

Da 1,5 a 3,8 volte l'assunzione. **Resta sotto la soglia di Gate 2** sul trade peggiore
(÷10 ≤ $500): $442. È la prima strategia della pipeline la cui unità di rischio entra nel
budget dell'MLL — le tre su @NQ morivano esattamente qui.

### Corretto: il profilo della variante A

| | spec (dalla ricerca del corso) | misurato (78 trade, 4 mesi) |
|---|---|---|
| WR variante A | ~34% | **57,7%** |
| avg win / avg loss | > 1 | 1,50 |
| PF | 1,18 (ricerca) / 1,64–3,28 (live) | 2,04 |

Il WR 34% non si riproduce. Ipotesi: il time exit a 10:00 CT chiude in piccolo utile
molte posizioni che altrimenti si girerebbero in perdita. Da verificare sui 5 anni dello
Stage 2.

**Conseguenza sulla pre-registrazione**: allo Stage 2 vanno **entrambe** le varianti, non
solo la B. La regola «Gate 2 si giudica sulla variante B» era motivata dall'attesa WR 34%
della A; quell'attesa è smentita da un dato di meccanica, non da una scelta a posteriori
sui risultati. Le varianti Stage 4 (`StopFrac` 0.5/0.75, long only, finestra 22:00–01:00)
restano come scritte.

### Aperto

- **ADR dell'oro nel periodo non misurata**: 37,8 punti di range asiatico su un
  sottostante a $4.100–4.400 vanno rapportati al range giornaliero medio. Se il range
  asiatico è una frazione dominante dell'ADR, lo stop «tutto il range» è strutturalmente
  sovradimensionato e la variante `StopFrac` < 1 diventa il caso base, non un'alternativa.
- **Gate date** non ancora eseguito.
