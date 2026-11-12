# I Colab della Live 003 contro `prop_sim.py` (24/10/2026)

**I notebook.** Recuperati dal video della Live 003: il link stava nella barra degli indirizzi.
Scaricati e salvati in `education/protocollo/8. Livestreaming/`, ciascuno con l'export `.py`
(solo sorgente):

| notebook | link |
|---|---|
| `PropFirm_MonteCarlo_Apex50K_1708.ipynb` (strategia singola) | https://colab.research.google.com/drive/1IvtqvVrsoDslpyp0f5NxlCwsNlwrZg8I |
| `PropFirm_MonteCarlo_Apex50K_1708_MultiStrats.ipynb` | https://colab.research.google.com/drive/1QBAWheDkYx8YBYQDGhuI1ExiG7jachTO |

Sono la versione riscritta di cui si parla nella Live 003. Quelli in `4. Validation…/` sono la
versione delle lezioni, che chiede ancora il CSV.

## Il motore è lo stesso

| | Colab (`ENGINE = "excursion"`) | `prop_sim.py` |
|---|---|---|
| ricampionamento | giorni con reimmissione, ordine dei trade dentro il giorno conservato | idem |
| dentro il trade | il minimo (Drawdown $ di MC) viene controllato **prima** della chiusura | idem |
| trailing | EOD, fermo dentro la giornata, si blocca a +$100 | idem (`LOCK` 50.100) |
| target | controllato solo alla chiusura dei trade | idem |

Su una strategia sola, quindi, i due danno la stessa risposta a parità di regole.

## Dove `prop_sim.py` è più avanti

- **Regole Lucid, non Apex.** Il Colab ha la scadenza a 21 giorni di Apex, che abbassa il
  pass rate. I numeri dei due non vanno confrontati direttamente.
- **Costi del micro.** Il Colab aggiunge $2,25 + $5 per NQ sopra il P&L del report (che ha già
  la commissione di MC) e poi scala in modo lineare: il costo per MNQ risulta $0,73, quello
  vero è ~$1,50. Noi togliamo `COMM_FULL` e applichiamo il costo del micro.
- **Degrado.** Il Colab ha `apply_day_degradation` ma nessuna cella la chiama con valori
  diversi da zero, e il motore excursion la ignora (`**kw`). Da noi i cinque scenari girano.
- **Correlazione fra tentativi.** Noi abbiamo il contiguo, il sequenziale e la partenza da un
  drawdown. Nel Colab il cumulato sui tentativi assume l'indipendenza: la cella "10b" citata
  nella Live 004 è successiva a questa versione.

## Cosa manca a noi, in ordine di utilità

1. **Il paniere di più strategie (il MultiStrats).** Ci servirà appena avremo una seconda
   strategia viva. Il metodo è pulito e va copiato così com'è:
   - finestra ristretta ai giorni in cui **tutte** le strategie erano attive;
   - matrice giorni × strategie: si sommano le strategie dello **stesso** giorno e non si
     ricampionano separatamente, così resta la correlazione vera;
   - dentro il giorno, i trade di tutte le strategie in ordine di orario, ciascuno col suo peso;
   - pesi: screening sullo Sharpe giornaliero, poi la short-list passa per il simulatore;
     **il peso uguale resta, a meno che il vincitore lo batta fuori dagli intervalli di
     confidenza** ("an optimized mix inside the noise is fitted noise").
2. ~~**L'intervallo di confidenza sul pass rate** (Wilson).~~ **Fatto il 24/10.** Misura il
   rumore della simulazione, non quello dei dati: lo dice anche l'output.
3. ~~**Sizing a gradini** (cella 8b).~~ **Fatto il 24/10**, sezione 6 di `prop_sim.py`. Su
   DriftPullback la risposta **dipende dalla guardia**: con 60 giorni partire da 1 micro
   costa −10 pp (33% contro 43%), con 250 giorni guadagna +10 pp (52% contro 42%). Il
   docente l'aveva previsto: senza scadenza il risultato può cambiare.
4. **Le regole delle prop in un file** (`prop_firms.ini`), con `--prop` e `--confronta`. Per
   ora LucidFlex 50k e Apex 50K EOD (questo dal Colab, da verificare).
5. **Il conto funded** (payout, ciclo di vita, inattività). Il Colab usa le regole Apex 4.0:
   per noi servono quelle di LucidFlex funded. Va fatto dopo aver passato l'eval.

## Differenze verificate che per noi non contano

- **Giorni feriali senza trade.** Il Colab li conta come giorni a zero, noi no. Su
  DriftPullback, nell'OOS, ci sono trade in 456 giorni su 466 feriali: la differenza è
  trascurabile.
- **Giornata Lucid contro data di calendario.** Entrambi raggruppano i trade per data di
  calendario. Per Lucid invece la giornata va dalle 18:00 alle 16:45 ET. DriftPullback entra ed
  esce fra le 9 e le 15 CT, dal lunedì al venerdì, quindi per lei non cambia niente. **Diventa un
  errore per una strategia con trade la sera**: Rebalancing, per esempio, sarebbe finita nel giorno
  sbagliato. Il Colab, in più, scarta i trade del sabato e della domenica.
