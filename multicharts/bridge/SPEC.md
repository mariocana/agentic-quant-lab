# Bridge MultiCharts → MT5 (bozza del 04/11/2026)

**A cosa serve.** Eseguire sui CFD di una prop i segnali calcolati su NQ e GC, senza riscrivere le
strategie. Il segnale resta quello del futures, con i suoi volumi. MT5 fa solo da esecutore.

**Stato: mai compilato né provato.** Né `MarioBridge.mq5`, né `Mario_Bridge.txt`, né le chiamate nei
segnali sono passati da un compilatore. Prima prova su challenge free.

**Una funzione per tutti.** I segnali chiamano `Mario_Bridge` (`Mario_Bridge.txt`): controlla che il
file sia impostato e che il calcolo sia in tempo reale, e scrive la riga. Il formato vive solo lì.
Per aggiungere una strategia bastano gli input `BridgeFile` e `BridgeMicro` e le chiamate.

```text
grafico MC → file nella cartella Common di MetaQuotes → MarioBridge.mq5 → conto CFD
```

## v2: bridge a stato (09/11/2026), sostituisce quello a eventi

**Perché.** Il bridge a eventi (sotto) non copia le uscite: MC chiude a fine barra, mentre il CFD
mette stop e target subito, dal suo fill, e il 05/11 un SL del grafico è diventato un TP sul CFD.
Il design di mc2mt5 copia invece la **posizione**. Il test del 09/11 con `Mario_PosTest` ha dato
il risultato: un indicatore a ogni tick vede la posizione della strategia cambiare **nel secondo del
fill**, anche a metà barra (uscite DPB alle 09:46:31 e 10:27:03). Serve l'automazione **accesa**
(SA o AA, anche con broker Paper Trader): ad automazione spenta la strategia si ricalcola a fine
barra.

```text
strategia sul grafico → Mario_BridgeStato (indicatore, ogni tick) → mario_stato_<STRAT>.csv
                      → MarioBridgeStato.mq5 (ogni secondo) → conto CFD
```

- **Il file:** una riga, riscritta a ogni cambio, `DPB;NQ;-1;120.00;FINE` = DPB short 1 micro,
  stop d'emergenza a 120 punti. Una riga senza `FINE`, o il file mancante mentre MC lo riscrive:
  si rilegge al secondo dopo.
- **L'EA agisce solo sui cambi.** Posizione voluta diversa dall'ultima letta: chiude il lato
  sbagliato e apre a mercato. Fino a 5 tentativi, poi si ferma fino al cambio successivo.
- **Niente riaperture.** Se lo stop d'emergenza chiude la posizione, l'EA non la riapre finché MC non
  cambia di nuovo. All'avvio non insegue niente: prende lo stato com'è e scrive nel log se MC e MT5
  sono diversi.
- **Una strategia = un magic** (`Magic` + posizione nella lista `Strategie`): non dipende dal
  commento, che i broker possono riscrivere. Conto hedging, come prima.
- **Stop d'emergenza sul server del broker**, circa 1,5 volte lo stop della strategia: protegge se
  MC, il VPS o la connessione cadono. Le uscite normali le decide MC. Senza target sul broker.
- **I segnali non si toccano.** Le chiamate a `Mario_Bridge` sono state tolte dai tre segnali il
  09/11 (tornati alle versioni prima del bridge). `Mario_Bridge.txt` e `MarioBridge.mq5` restano solo
  come storia della v1.
- **Cambi di size dentro un trade non si copiano** (stesso lato, più micro): nessuna delle tre
  strategie li fa.

| grafico | Strat | Strum | StopEmergenzaPts | perché |
|---|---|---|---|---|
| `Drift_LIVE` | DPB | NQ | 120 | stop fisso 80 |
| `Mario_OvernightBiasORB` | OBO | NQ | 300 | stop 0,30 × ATR, oggi ~200 |
| `MarioGoldAsianRange` | GAR | GC | 60 | stop = range, al massimo ~1% (~40 punti) |

**Installazione v2.**
1. **Togliere `MarioBridge` (v1) da MT5** e ricompilare i tre segnali in MC dalla versione del repo,
   senza bridge.
2. `MarioBridgeStato.mq5` in `MQL5/Experts`, F7, su un grafico qualsiasi, *Algo Trading* acceso.
   Nel log d'avvio deve leggersi `margine: hedging`.
3. PowerLanguage Editor: **New → Indicator** `Mario_BridgeStato`, compila. Sui tre grafici, accanto
   alla strategia, con gli input della tabella e **Update on every tick** acceso.
4. Automazione accesa su tutti e tre i grafici. Senza conto futures: broker **Paper Trader**.

**Il test v2:** le stesse soglie sotto, più due conteggi. Uscite a metà barra del grafico contro quelle
del CFD, con la differenza di orario. Stop d'emergenza scattati: dovrebbero essere zero.

## v1: bridge a eventi (04/11/2026)

## Il formato

Una riga per evento, `azione;id;strategia;strumento;lato;micro;stop;target;FINE`. Gli ordini stop
di Gold hanno due campi in più, le distanze dei bordi dal prezzo:

```text
APRI;OBO-1261105-1015;OBO;NQ;1;1;120.50;361.50;FINE
PENDENTE;GAR-1261105-15;GAR;GC;0;1;24.00;0;11.50;12.50;FINE
CHIUDI;OBO-1261105-1015;OBO;NQ;0;0;0;0;FINE
```

**Gold: due ordini stop OCO.** L'EA li mette a prezzo CFD ± distanza, perché GC e XAUUSD hanno
prezzi diversi: quando uno riempie cancella l'altro. Se il prezzo è già oltre il bordo, entra a
mercato, come farebbe MultiCharts. Variante A: nessun target, uscita a tempo con `CHIUDI`.

- **Stop e target sono distanze in punti**, calcolate dal fill sul CFD: NQ e US100 hanno prezzi
  diversi. Stanno sul server del broker, non emulate.
- **Una riga a metà** (senza `FINE`) si rilegge al giro dopo.
- **All'avvio l'EA salta tutto il file:** un segnale vecchio non si esegue mai. Le posizioni aperte
  restano protette dal loro stop, e si chiudono con l'`id` nel commento.

## Lotto equivalente al micro

`lotti = micro × $ al punto del micro ÷ ($ al punto per lotto)`, letti da `SYMBOL_TRADE_TICK_VALUE`
e `SYMBOL_TRADE_TICK_SIZE`. 1 MNQ = $2 al punto, 1 MGC = $10. Scarto oltre il 5% per il passo dei
lotti: avviso nel log. **Conto in USD**, altrimenti il valore del punto segue il cambio.

## Installazione sul VPS

1. MT5 sullo stesso VPS, login sul conto free.
2. `MarioBridge.mq5` in `MQL5/Experts`, compilare in MetaEditor (F7), trascinarlo su **un** grafico
   qualsiasi, *Algo Trading* acceso.
3. Controllare il nome dei simboli in Market Watch (`SimboloNQ`, `SimboloGC`).
4. In PowerLanguage Editor: **New → Function**, nome `Mario_Bridge`, Return Type **Numeric**, incolla
   `Mario_Bridge.txt`, compila. **Prima dei segnali**, che senza non compilano.
5. Su `Drift_LIVE`, `Mario_OvernightBiasORB` e `MarioGoldAsianRange` l'input `BridgeFile` =
   `C:\Users\<utente>\AppData\Roaming\MetaQuotes\Terminal\Common\Files\mario_bridge.csv`.
6. Il pulsante di automazione di MultiCharts può restare **spento**: il segnale scrive il file lo
   stesso, in tempo reale. Non su backtest o ricalcolo.

## Il test, scritto prima di partire

**Domanda:** il CFD replica il futures, a un costo che l'edge regge?

**DPB, Overnight Bias e Gold insieme.** DPB e Overnight Bias sono sullo stesso US100: serve un conto
**hedging**, con due posizioni separate. Soglia di Gold: entro **$10 per micro** su $47 di avg OOS,
con lo stesso criterio. **Soglia di DPB: entro $2 per micro** su $5,70 di avg OOS, cioè l'edge deve
restare sopra i due terzi; in punti di US100 vuol dire al massimo 1 punto di costo in più. Un ordine stop sul CFD può scattare quando quello sul grafico
non scatta, e viceversa: è il rischio specifico, si conta a parte quante volte succede.

**Si misura per ogni trade**, da `mario_bridge_fill.csv` e dalla storia MT5, contro il grafico:
ritardo del fill, spread al fill, P&L in punti.

| esito dopo almeno 30 trade | criterio |
|---|---|
| **va** | P&L medio del CFD entro **$10 per micro** dal grafico (~20% dell'avg OOS di $49) |
| **non va** | scarto oltre $25 per micro, o trade mancanti o doppi: si capisce perché prima di andare avanti |
| in mezzo | altri 30 trade |

**Le challenge free illimitate misurano l'esecuzione, non il pass rate.** Si tengono tutte nel
conteggio: ripeterle finché una passa dimostrerebbe solo che si è ripetuto. L'esecuzione di un
conto free può essere diversa da quella di uno pagato.

## Da controllare sul conto free

- [ ] conto in modalità hedging, non netting: DPB e Overnight Bias vanno tenute separate
- [ ] il commento dell'ordine resta sulla posizione: `CHIUDI` lo usa per trovarla
- [ ] specifiche di US100 e XAUUSD: valore del punto, spread, commissioni, orari
- [ ] regole su EA, copiatori e operazioni uguali su più prop
- [ ] quando FTMO azzera la perdita giornaliera (Gold apre di notte)
- [ ] news e weekend sul funded
- [ ] licenza MultiCharts: scade il 29/11
