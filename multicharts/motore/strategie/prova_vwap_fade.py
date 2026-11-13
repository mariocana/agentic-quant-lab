"""prova_vwap_fade (ricerca/idee/prova_vwap_fade/hypothesis.md, «Regola eseguibile»).

Fade della banda VWAP +/- 1 sigma su NQ, sessione regolare 08:30-15:00 CT.
data1 = barre da 5 minuti (esecuzione), data2 = barre da 1 minuto (VWAP e sigma pesati per volume:
le barre da 1 minuto dentro una barra da 5 non portano il volume, quindi servono come seconda serie).

- VWAP e sigma ancorati alle 08:30 e azzerati ogni giorno, dai minuti 08:31-15:00 (etichetta =
  chiusura), con p = (H+L+C)/3: VWAP = sum(v*p)/sum(v), sigma = sqrt(sum(v*(p-VWAP)^2)/sum(v)).
  Alla chiusura di una barra da 5 minuti contano tutti i minuti fino a quella chiusura compresa.
- Corto: chiusura > VWAP + 1 sigma e chiusura precedente (nella sessione) <= la sua banda; la prima
  barra (08:35) vale come attraversamento fresco. Lungo: lo specchio.
- Una posizione per volta. A ogni ingresso entrambi i lati si disarmano; un lato si riarma quando
  una barra chiude dentro la sua banda con la posizione flat. Poi serve l'attraversamento fresco.
- Ingresso a mercato alla barra dopo; target (limite) VWAP0 e stop VWAP0 +/- 2.5 sigma0, messi
  insieme all'ingresso (attivi gia' nella barra del fill, come OBO-L-SL0) e poi ripetuti.
  Stop e target nello stesso minuto: decide il percorso del Bar Magnifier del motore, NON «vince lo
  stop» come chiede la regola (il motore non lo permette senza cambiare motore.py: vedi il desk).
- Segnali sulle barre che chiudono 08:35-14:55. Alla chiusura della barra delle 15:00 la posizione
  si chiude a mercato (fill all'apertura della barra dopo, cioe' alla chiusura delle 15:00).
"""
import math

DEFAULT = dict(SessStart=830, SessEnd=1500, LastSignal=1455, BandK=1.0, StopK=2.5,
               TradeLongs=True, TradeShorts=True, Cts=1)


class VwapFade:
    def __init__(self, barre1m, **inp):
        self.p = dict(DEFAULT, **inp)
        self.m1 = barre1m
        self.j = -1                       # indice dell'ultima barra da 1 minuto letta
        self.dataPrec = None
        self.sV = self.sVP = self.sVP2 = 0.0
        self.vwap = self.sigma = 0.0
        self.prevC = None                 # chiusura della barra da 5 minuti precedente, in sessione
        self.prevUp = self.prevDn = 0.0   # sue bande
        self.armL = self.armS = True
        self.stopPx = self.tgtPx = 0.0

    def _nuovo_giorno(self):
        self.sV = self.sVP = self.sVP2 = 0.0
        self.ref = None                   # prezzo di riferimento: somme centrate, sigma senza cancellazione
        self.vwap = self.sigma = 0.0
        self.prevC = None
        self.armL = self.armS = True

    def su_barra(self, ctx):
        p, b = self.p, ctx.b()
        t = b.ora

        if b.data != self.dataPrec:
            self._nuovo_giorno()
            self.dataPrec = b.data

        # minuti della sessione fino alla chiusura di questa barra
        while self.j + 1 < len(self.m1) and self.m1[self.j + 1].t <= b.t:
            self.j += 1
            m = self.m1[self.j]
            if m.data == b.data and p['SessStart'] < m.ora <= p['SessEnd'] and m.v > 0:
                if self.ref is None:
                    self.ref = m.o
                tp = (m.h + m.l + m.c) / 3 - self.ref
                self.sV += m.v
                self.sVP += m.v * tp
                self.sVP2 += m.v * tp * tp

        mp = ctx.market_position

        if mp != 0:
            if t >= p['SessEnd']:
                ctx.sell('L.Flat')
                ctx.buy_to_cover('S.Flat')
            elif mp == 1:
                ctx.sell('L.SL', self.stopPx, 'stop')
                ctx.sell('L.TP', self.tgtPx, 'limite')
            else:
                ctx.buy_to_cover('S.SL', self.stopPx, 'stop')
                ctx.buy_to_cover('S.TP', self.tgtPx, 'limite')

        if not (p['SessStart'] < t <= p['SessEnd']) or self.sV <= 0:
            return

        mu = self.sVP / self.sV
        self.vwap = self.ref + mu
        self.sigma = math.sqrt(max(self.sVP2 / self.sV - mu * mu, 0.0))
        up = self.vwap + p['BandK'] * self.sigma
        dn = self.vwap - p['BandK'] * self.sigma

        if mp == 0:
            if b.c <= up:
                self.armS = True
            if b.c >= dn:
                self.armL = True

        freshS = self.prevC is None or self.prevC <= self.prevUp
        freshL = self.prevC is None or self.prevC >= self.prevDn
        self.prevC, self.prevUp, self.prevDn = b.c, up, dn

        if mp != 0 or t > p['LastSignal'] or self.sigma <= 0:
            return

        if p['TradeShorts'] and self.armS and freshS and b.c > up:
            self.stopPx, self.tgtPx = self.vwap + p['StopK'] * self.sigma, self.vwap
            ctx.sell_short('VwapFade.S', p['Cts'])
            ctx.buy_to_cover('S.SL', self.stopPx, 'stop')
            ctx.buy_to_cover('S.TP', self.tgtPx, 'limite')
            self.armS = self.armL = False
        elif p['TradeLongs'] and self.armL and freshL and b.c < dn:
            self.stopPx, self.tgtPx = self.vwap - p['StopK'] * self.sigma, self.vwap
            ctx.buy('VwapFade.L', p['Cts'])
            ctx.sell('L.SL', self.stopPx, 'stop')
            ctx.sell('L.TP', self.tgtPx, 'limite')
            self.armS = self.armL = False
