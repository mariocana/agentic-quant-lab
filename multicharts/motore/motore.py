"""Backtest a barre con la semantica di MultiCharts (modalita' Classic, IOG spento, Bar Magnifier).

- La strategia gira alla CHIUSURA di ogni barra e mette ordini validi solo per la barra dopo, come
  in EasyLanguage: un ordine non ripetuto decade.
- `mercato`: eseguito all'apertura della barra dopo.
- `stop` / `limite`: cercati dentro la barra dopo sulle barre da 1 minuto. In ogni minuto il prezzo
  va open -> estremo piu' vicino all'open -> l'altro -> close (regola del Bar Magnifier di MC).
  Stop: al prezzo dello stop, o all'apertura del minuto se ci e' gia' oltre. Limite: al tocco, al
  prezzo del limite o migliore.
- Le uscite le mette la strategia dalla chiusura della barra d'ingresso in poi: nella barra in cui
  entra non c'e' ancora nessuno stop, esattamente come in MC.
- `esci_a_chiusura`: SetExitOnClose, flat alla chiusura dell'ultima barra della sessione.
- P&L in punti; i dollari li fa `Trade.dollari` con valore del punto e commissione per lato.
"""
import datetime as dt


class Ordine:
    __slots__ = ('tipo', 'lato', 'qta', 'prezzo', 'nome', 'uscita')

    def __init__(self, tipo, lato, qta, prezzo, nome, uscita):
        self.tipo, self.lato, self.qta, self.prezzo, self.nome, self.uscita = tipo, lato, qta, prezzo, nome, uscita


class Trade:
    __slots__ = ('lato', 'qta', 't_in', 'p_in', 'nome_in', 't_out', 'p_out', 'nome_out', 'su', 'giu')

    def __init__(self, lato, qta, t_in, p_in, nome_in):
        self.lato, self.qta, self.t_in, self.p_in, self.nome_in = lato, qta, t_in, p_in, nome_in
        self.t_out = self.p_out = self.nome_out = None
        self.su = self.giu = 0.0                 # escursione favorevole / avversa, in punti

    @property
    def punti(self):
        return (self.p_out - self.p_in) * self.lato

    def dollari(self, punto, comm_lato):
        return self.punti * punto * self.qta - 2 * comm_lato * self.qta

    def __repr__(self):
        return 'Trade(%s %+d %s@%.2f -> %s %s@%.2f = %.2f pt)' % (
            self.nome_in, self.lato, self.t_in, self.p_in, self.nome_out, self.t_out, self.p_out, self.punti)


class Contesto:
    """Quello che la strategia vede alla chiusura della barra i."""

    def __init__(self, barre, punto, comm_lato):
        self.barre = barre
        self.i = 0
        self.pos = 0                 # contratti con segno
        self.trade = None            # trade aperto
        self.chiusi = []
        self.ordini = []
        self.punto, self.comm_lato = punto, comm_lato

    # --- stato, nomi di EasyLanguage ---
    @property
    def market_position(self):
        return (self.pos > 0) - (self.pos < 0)

    @property
    def entry_price(self):
        return self.trade.p_in if self.trade else 0.0

    @property
    def total_trades(self):
        return len(self.chiusi)

    def position_profit(self, n=1):
        """PositionProfit(n): P&L in $ del trade chiuso n posizioni fa, commissioni comprese."""
        if len(self.chiusi) < n:
            return 0.0
        return self.chiusi[-n].dollari(self.punto, self.comm_lato)

    def b(self, k=0):
        return self.barre[self.i - k]

    # --- ordini per la barra dopo ---
    def buy(self, nome, qta=1, prezzo=None, tipo='mercato'):
        self.ordini.append(Ordine(tipo, 1, qta, prezzo, nome, False))

    def sell_short(self, nome, qta=1, prezzo=None, tipo='mercato'):
        self.ordini.append(Ordine(tipo, -1, qta, prezzo, nome, False))

    def sell(self, nome, prezzo=None, tipo='mercato'):
        self.ordini.append(Ordine(tipo, -1, 0, prezzo, nome, True))

    def buy_to_cover(self, nome, prezzo=None, tipo='mercato'):
        self.ordini.append(Ordine(tipo, 1, 0, prezzo, nome, True))


def _percorso(o, h, l, c):
    return (o, h, l, c) if abs(o - h) <= abs(o - l) else (o, l, h, c)


class Motore:
    def __init__(self, barre, strategia, punto=20.0, comm_lato=0.0, esci_a_chiusura=True,
                 pausa_sessione=dt.timedelta(minutes=30)):
        self.barre, self.s = barre, strategia
        self.ctx = Contesto(barre, punto, comm_lato)
        self.esci_a_chiusura, self.pausa = esci_a_chiusura, pausa_sessione

    # --- esecuzione ---
    def _apri(self, lato, qta, t, p, nome):
        ctx = self.ctx
        ctx.pos = lato * qta
        ctx.trade = Trade(lato, qta, t, p, nome)

    def _chiudi(self, t, p, nome):
        ctx = self.ctx
        tr = ctx.trade
        tr.t_out, tr.p_out, tr.nome_out = t, p, nome
        ctx.chiusi.append(tr)
        ctx.trade, ctx.pos = None, 0

    def _esegui(self, o, t, p):
        """Un ordine scattato al prezzo p. Ritorna True se ha cambiato la posizione."""
        ctx = self.ctx
        mp = ctx.market_position
        if o.uscita:
            if mp == 0 or mp == o.lato:          # Sell da long, BuyToCover da short
                return False
            self._chiudi(t, p, o.nome)
            return True
        if mp == o.lato:                         # gia' dentro da quel lato: niente piramidi
            return False
        if mp != 0:                              # inversione
            self._chiudi(t, p, o.nome)
        self._apri(o.lato, o.qta, t, p, o.nome)
        return True

    def _scatta(self, o, a, b, primo):
        """Prezzo a cui l'ordine o scatta sul tratto a -> b (primo: a e' l'apertura del minuto)."""
        compra = o.lato > 0
        if o.tipo == 'stop':
            if compra:
                if primo and a >= o.prezzo:
                    return a
                if b >= o.prezzo > a:
                    return o.prezzo
            else:
                if primo and a <= o.prezzo:
                    return a
                if b <= o.prezzo < a:
                    return o.prezzo
        else:                                    # limite
            if compra:
                if primo and a <= o.prezzo:
                    return a
                if b <= o.prezzo < a:
                    return o.prezzo
            else:
                if primo and a >= o.prezzo:
                    return a
                if b >= o.prezzo > a:
                    return o.prezzo
        return None

    def _attivo(self, o):
        mp = self.ctx.market_position
        if o.uscita:
            return mp != 0 and mp != o.lato
        return mp != o.lato

    def _barra(self, bar, ordini):
        ctx = self.ctx
        for o in [o for o in ordini if o.tipo == 'mercato']:
            self._esegui(o, bar.t, bar.o)
        pend = [o for o in ordini if o.tipo != 'mercato']
        for o1, h1, l1, c1 in bar.sub:
            if ctx.trade:                        # escursioni del trade aperto
                tr = ctx.trade
                fav = (h1 - tr.p_in) if tr.lato > 0 else (tr.p_in - l1)
                avv = (l1 - tr.p_in) if tr.lato > 0 else (tr.p_in - h1)
                tr.su, tr.giu = max(tr.su, fav), min(tr.giu, avv)
            if not pend:
                continue
            p = _percorso(o1, h1, l1, c1)
            for k in range(3):
                a, b, primo = p[k], p[k + 1], k == 0
                # tutti gli ordini attivi che scattano su questo tratto; vince il primo toccato
                while True:
                    cand = []
                    for o in pend:
                        if not self._attivo(o):
                            continue
                        px = self._scatta(o, a, b, primo)
                        if px is not None:
                            cand.append((abs(px - a), px, o))
                    if not cand:
                        break
                    cand.sort(key=lambda x: x[0])
                    _, px, o = cand[0]
                    pend.remove(o)
                    self._esegui(o, bar.t, px)
                    a, primo = px, False         # il resto del tratto riparte dal fill

    def gira(self, dal=None):
        """dal: datetime da cui la strategia puo' operare (prima solo riscaldamento)."""
        ctx, n = self.ctx, len(self.barre)
        for i, bar in enumerate(self.barre):
            ordini, ctx.ordini = ctx.ordini, []
            if dal is None or bar.t >= dal:
                self._barra(bar, ordini)
            ctx.i = i
            self.s.su_barra(ctx)
            if dal is not None and bar.t < dal:
                ctx.ordini = []
            ultima = i == n - 1 or self.barre[i + 1].t - bar.t > self.pausa
            if self.esci_a_chiusura and ultima and ctx.trade:
                self._chiudi(bar.t, bar.c, 'EOD')
                ctx.ordini = []
        if ctx.trade:                            # aperto a fine dati: chiuso all'ultimo close
            self._chiudi(self.barre[-1].t, self.barre[-1].c, 'FINE')
        return ctx.chiusi
