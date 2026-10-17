# Overnight-Intraday Reversal — Stage 0

**Aperta il 17/10/2026** come **seconda gamba** del basket. Decisione: non si parte con
DriftPullback da sola (Live 004: *"don't run a single strategy even in the evaluation
phase"*).

## Ipotesi, e la ragione strutturale

Il movimento fatto **di notte** e in parte **sbilanciamento di flusso impaziente**, non
informazione: chi deve entrare o uscire fuori orario paga uno spread largo e un book sottile,
e chi fornisce quella liquidita viene **ripagato alla riapertura**, quando il flusso normale
torna. La reversione non e una regolarita statistica che puo svanire: e il **compenso per un
servizio**, come il VWAP e un benchmark contabile e non un pattern.

**Fonte:** Liu, Liu, Wang, Zhou, Zhu — *Overnight-Intraday Reversal Everywhere*, AsianFA 2025.
Livello 2: evidenza cross-asset dichiarata, non replicata da noi.

## Perche questa e non le altre due

| candidata | finestra | nota |
|---|---|---|
| **Overnight reversal** | **apertura** | **cade nell'ora libera**, meccanismo strutturale, fonte recente e cross-asset |
| Gap fade | apertura | stessa finestra, ma Grant-Wolf-Yu 2005 dice che l'edge si riduce molto coi costi e Iwanaga-Sakemoto 2026 che si indebolisce dopo il 2010 |
| Morning momentum / afternoon reversal | pomeriggio | sovrapposizione piena con DriftPullback |

**«L'ora libera»** e un dato, non una speranza: la distribuzione oraria degli ingressi di
DriftPullback sull'OOS parte dall'ora delle **09:00** (il suo `SessStart` e 09:30), mentre RTH
apre alle **08:30**. Fra 08:30 e 09:30 CT **non ha un solo trade**. Una strategia che si
risolve li ha correlazione quasi nulla **per costruzione**: non puo essere in posizione nello
stesso momento.

## Geometria, pre-registrata e non ottimizzabile

```
G        = prezzo d'ingresso - chiusura RTH di ieri
ingresso = chiusura della prima barra di sessione, CONTRO G
target   = ingresso - 0,50 * G        (meta ritracciamento)
stop     = ingresso + 0,75 * G
```

| | valore |
|---|---|
| **R:R** | 0,50 / 0,75 = **0,667** — dentro la banda prop |
| **caso** | 0,75 / (0,75 + 0,50) = **60%** |
| **soglia** | WR >= 66%, cioe **eccesso >= +6 pp** |

Gate d'ingresso: `|G| >= 0,15 x range medio delle ultime 20 sessioni`. Serve a saltare i
giorni senza gap, dove si fadrebbe rumore.

## Le soglie, e sono due diverse da quelle di una strategia sola

**Questa e una SECONDA gamba: non deve reggere il conto, deve aggiungere.**

- per **bastare da sola** a ~1 setup/giorno servirebbero **+7,6 pp** (vedi
  `mc/docs/seconda_gamba.md`): fuori portata, il nostro record e +5,3;
- per **valere come seconda gamba** serve un **eccesso positivo a >= 3 errori standard da
  zero**, piu bassa correlazione.

**Ma non basta che sia positivo in media: deve essere positivo con n sufficiente.** Una gamba
a edge zero **peggiora** il basket — provato aggiungendo VaultBreak.

## Strumento: @RTY, con @YM come controllo

| | @RTY / M2K | @YM / MYM |
|---|---|---|
| R/ATR a R=$80 | **0,49** (il migliore dei cinque) | 0,47 |
| stabilita di regime 2026 vs 2020-24 | **1,15x** (il piu stabile) | 1,39x |
| costo | $0,50/lato | $0,50/lato |
| liquidita | **la peggiore dei micro indici** | migliore |

**RTY e il piu domestico dei cinque indici**: il suo overnight e meno guidato da notizie
globali e piu da sbilanciamento di flusso, che e esattamente il meccanismo del paper. **Ma e
mio ragionamento, non una misura** — la misura lo testera.

**L'avvertenza che pesa**: M2K e il micro indice **meno liquido**, e questa strategia opera
**all'apertura**, quando lo spread e piu largo. Si citano 1 tick in RTH e 2 fuori orario: su
R = $80 sarebbero ~5% di costo andata e ritorno. **Va modellato, non assunto.** Per questo YM
gira nello stesso pomeriggio: se RTY vince sull'eccesso ma perde sui costi reali, il confronto
lo dice — come e successo con CL e YM, dove la misura ha ribaltato la mia stima del 18%.

## Come si misura

`ON_Reversal_Study.txt` e un **indicatore**, non una strategia. Riporta:

1. **frequenza** — quanti giorni hanno un gap sopra la soglia;
2. **R per micro in dollari** — decide quanti contratti stanno nell'MLL;
3. **eccesso sul caso**, separato per **prima ora** e **fine giornata**: la prima dice se la
   correlazione resta nulla, la seconda se il ritracciamento ha solo bisogno di piu tempo;
4. **`R:R realizzato`**, che **deve valere ~0,667**. Qui le distanze sono proporzionali a G
   per costruzione, quindi se non torna qualcosa e rotto e **il resto del log non si legge**.

Chart 5 min, timezone **Exchange (CT)**, periodo **2020-2024**, `ShowLog 1`. La sessione la
impone il codice, non il template. Lead-in: 20 sessioni.

## Aspettativa dichiarata, prima del run

**Eccesso fra +1 e +4 pp sulla prima ora**, cioe **sotto la soglia dei +6** ma **sopra zero**
— quindi potenzialmente utile come seconda gamba e inutile come prima. E la banda in cui e
caduto tutto quello che abbiamo misurato (+0,4 … +5,3), e non ho ragione di aspettarmi che
questo meccanismo esca dal gruppo.

**Sulla fine giornata mi aspetto un eccesso piu alto della prima ora**, perche il
ritracciamento ha piu tempo per compiersi. Se succede, e un compromesso da decidere: piu edge
contro piu correlazione con DriftPullback.

## Misura 2020-2024: **non raggiunge la soglia**, ma e il miglior segnale mai trovato

Log: `mc/docs/measures/on_reversal_YM_2020-2024.txt` e `..._RTY_...`. 1.293 sessioni.

**`R:R realizzato 0,667` su entrambi**: stavolta lo strumento misura quello che deve.

### Prima ora (08:30-09:30, la finestra libera)

| | n risolti | aperti | WR | **eccesso** | errori standard | IC 95% |
|---|---|---|---|---|---|---|
| **@YM** | 652 | 222 | **64,11%** | **+4,11 pp** | **2,14** | +0,35 … +7,87 |
| @RTY | 724 | 167 | 61,46% | +1,46 pp | 0,80 | −2,10 … +5,03 |

### Fine giornata

| | n risolti | WR | eccesso | errori standard |
|---|---|---|---|---|
| @YM | 821 | 62,00% | +2,00 pp | 1,17 |
| @RTY | 846 | 59,69% | **−0,31 pp** | −0,18 |

### Due mie previsioni smentite, e la seconda e una buona notizia

**1. Avevo scelto @RTY.** Ragionamento: indice piu domestico → overnight piu sbilanciamento di
flusso e meno informazione → meccanismo del paper piu forte. **Misurato: YM batte RTY quasi
3 a 1** (+4,11 contro +1,46). Il ragionamento era plausibile e sbagliato, e la misura lo
dice: era il motivo per far girare entrambi.

**2. Mi aspettavo l'eccesso piu alto a fine giornata**, perche il ritracciamento ha piu tempo.
**E il contrario**: YM passa da +4,11 a +2,00, RTY da +1,46 a −0,31. **L'edge sta nella prima
ora e si consuma.** Ed e esattamente la finestra dove DriftPullback non opera: **la cosa che
rende la correlazione nulla e anche la cosa che contiene l'edge.**

### Ma la soglia pre-registrata non e raggiunta, e va detto

Avevo scritto **«eccesso positivo a >= 3 errori standard da zero»**. YM sta a **2,14**.
L'intervallo di confidenza esclude lo zero (+0,35 … +7,87), ma **la soglia era mia e non
e passata.** Accettare 2,14 adesso sarebbe esattamente quello che abbiamo rimproverato a ogni
risultato comodo.

**E c'e una seconda riserva, onesta**: i **222 setup non risolti** entro la prima ora sono il
**25% del totale** e restano fuori dal win rate. In una strategia vera uscirebbero flat alle
09:30 con un P&L che non abbiamo misurato.

### Quello che regge, comunque

- **R per micro $74,60** su YM: dentro il budget, decide i contratti senza forzature.
- **0,69 setup/giorno**: basso, ma per una seconda gamba e accettabile — non deve reggere il
  conto, deve aggiungere.
- **Gap medio $99,47 per micro**, cioe il movimento che si fada e grande abbastanza da non
  essere rumore.

### La prossima misura, e perche non brucia l'OOS

**Rigirare su @YM il periodo 2016-2019**, che **non abbiamo mai usato**: non e l'out-of-sample
(2025-2026), e un pezzo di storia precedente all'IS. Se l'eccesso regge intorno a +4 pp, il
campione passa da 652 a **~1.282 risolti**, l'errore standard da 1,92 a **1,37**, e il
risultato arriva **esattamente a 3,00 errori standard**: la soglia pre-registrata, raggiunta
con dati veri invece che abbassando l'asticella.

Se invece sul 2016-2019 l'eccesso sparisce, la risposta e altrettanto chiara e costa un run.
