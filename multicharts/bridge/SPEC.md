# Bridge MultiCharts → MT5 (bozza del 04/11/2026)

**A cosa serve.** Eseguire sui CFD di una prop i segnali calcolati su NQ e GC, senza riscrivere le
strategie. Il segnale resta quello del futures, con i suoi volumi. MT5 fa solo da esecutore.

**Stato: mai compilato né provato.** Né `MarioBridge.mq5` né le righe in `OvernightBiasORB.txt`
sono passati da un compilatore. Prima prova su challenge free.

```text
grafico MC → file nella cartella Common di MetaQuotes → MarioBridge.mq5 → conto CFD
```

## Il formato

Una riga per evento, `azione;id;strategia;strumento;lato;micro;stop;target;FINE`:

```text
APRI;OBO-1261105-1015;OBO;NQ;1;1;120.50;361.50;FINE
CHIUDI;OBO-1261105-1015;OBO;NQ;0;0;0;0;FINE
```

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
4. Su `Mario_OvernightBiasORB` l'input `BridgeFile` =
   `C:\Users\<utente>\AppData\Roaming\MetaQuotes\Terminal\Common\Files\mario_bridge.csv`.
5. Il pulsante di automazione di MultiCharts può restare **spento**: il segnale scrive il file lo
   stesso, in tempo reale. Non su backtest o ricalcolo.

## Il test, scritto prima di partire

**Domanda:** il CFD replica il futures, a un costo che l'edge regge?

**Prima Overnight Bias**, poi Gold (ordini stop ai bordi del range: vanno aggiunti gli ordini pendenti).

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

- [ ] specifiche di US100 e XAUUSD: valore del punto, spread, commissioni, orari
- [ ] regole su EA, copiatori e operazioni uguali su più prop
- [ ] quando FTMO azzera la perdita giornaliera (Gold apre di notte)
- [ ] news e weekend sul funded
- [ ] licenza MultiCharts: scade il 29/11
