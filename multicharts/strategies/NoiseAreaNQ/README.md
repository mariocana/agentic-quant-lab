# NoiseAreaNQ — archiviata senza run (05/11/2026)

Strategy of the Month ottobre 2026 (@Ron Yitzhaki): net +$6.335, PF 1,30, Sharpe 3,7, periodo non
dichiarato. Fonte: `protocollo/10. Strategy of the Month/6. October 2026.pdf`, dal paper di
Zarattini, Aziz e Barbon (2024). Codice: `NoiseAreaNQ.txt`, in MultiCharts `Mario_NoiseAreaNQ`.

**Non è il codice dell'autore.** Il PDF lo mette in The Bridge, ma nella nostra copia non c'è: è
scritto dalla descrizione e **non è stato compilato**. Il caso BTC di settembre mostra che PDF e
codice possono non coincidere.

**Scelte che il PDF non fissa:**
- distanza dall'open in **punti**, non in percentuale (il paper usa la percentuale);
- sessione RTH 08:30–15:00 CT, 26 slot da 15 minuti;
- nessun limite di trade al giorno (`MaxTradesPerDay 0`): dopo un'uscita si può rientrare;
- niente ingressi da `FlatTime`; il flat parte dalla barra delle 14:30.

**Perché saltata:** stessa famiglia noise band di VaultBreak su NQ e sullo stesso OOS 2025–26, e
geometria simile a DriftPullback. Con stop 50 e target 25 il pareggio è intorno al 68% di trade
vinti. L'unico elemento nuovo è la banda che cambia con l'orario.
