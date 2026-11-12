"""PYTHONPATH=multicharts python3 -m unittest motore.test_misura -v

La calibrazione ha bisogno dei dati (quantlake/data/multicharts/NQ_1min.csv): senza, si salta.
"""
import os, unittest

from . import dati
from .misura import misura, misura_strategia


class Definizione(unittest.TestCase):
    def test_a_pareggio_l_eccesso_e_zero(self):
        # target 40, stop 80: il caso vince 2 volte su 3. 200 vinti e 100 persi = pareggio.
        m = misura([40.0] * 200 + [-80.0] * 100, 100)
        self.assertAlmostEqual(m['null'], 2 / 3)
        self.assertAlmostEqual(m['eccesso_pp'], 0.0)
        self.assertAlmostEqual(m['media_per_trade'], 0.0)

    def test_cambiare_il_rapporto_target_stop_non_crea_eccesso(self):
        # Stesso segnale senza edge, due geometrie: WR diverso, eccesso sempre zero.
        stretto = misura([20.0] * 400 + [-80.0] * 100, 100)
        largo = misura([80.0] * 100 + [-20.0] * 400, 100)
        self.assertGreater(stretto['wr'], 0.75)
        self.assertLess(largo['wr'], 0.25)
        self.assertAlmostEqual(stretto['eccesso_pp'], 0.0)
        self.assertAlmostEqual(largo['eccesso_pp'], 0.0)

    def test_il_segno_dell_eccesso_e_quello_della_media(self):
        su = misura([40.0] * 210 + [-80.0] * 90, 100)
        giu = misura([40.0] * 190 + [-80.0] * 110, 100)
        self.assertGreater(su['eccesso_pp'], 0)
        self.assertGreater(su['media_per_trade'], 0)
        self.assertLess(giu['eccesso_pp'], 0)
        self.assertLess(giu['media_per_trade'], 0)

    def test_i_trade_chiusi_a_tempo_contano(self):
        # Il difetto 2 del 17/10: i non risolti sono perdenti per costruzione. Qui entrano.
        senza = misura([40.0] * 200 + [-80.0] * 100, 100)
        con = misura([40.0] * 200 + [-80.0] * 100 + [-15.0] * 120, 100)
        self.assertLess(con['eccesso_pp'], senza['eccesso_pp'])

    def test_frequenza_e_dollari_al_giorno(self):
        m = misura([100.0] * 60 + [-50.0] * 40, 50)        # media 40 a trade, 2 trade al giorno
        self.assertAlmostEqual(m['trade_al_giorno'], 2.0)
        self.assertAlmostEqual(m['dollari_al_giorno_per_micro'], 8.0)

    def test_senza_vinti_o_senza_persi_non_si_misura(self):
        with self.assertRaises(ValueError):
            misura([10.0, 20.0, 30.0], 3)


@unittest.skipUnless(os.path.exists(dati.file_1min('NQ')), 'mancano i dati di NQ')
class Calibrazione(unittest.TestCase):
    """DriftPullback sull'IS 2020-2024, SPEC.md (tabella dello Stage 2, DriftMode 0):
    3.499 trade, WR 63,5%, R:R 0,640, null 61,0%, eccesso +2,6 pp, t 3,01."""

    @classmethod
    def setUpClass(cls):
        cls.m = misura_strategia('dpb')

    def test_ritrova_l_eccesso_della_spec(self):
        self.assertAlmostEqual(self.m['eccesso_pp'], 2.6, delta=0.1)

    def test_ritrova_wr_rr_e_null(self):
        self.assertAlmostEqual(100 * self.m['wr'], 63.5, delta=0.1)
        self.assertAlmostEqual(self.m['rr'], 0.640, delta=0.005)
        self.assertAlmostEqual(100 * self.m['null'], 61.0, delta=0.1)

    def test_ritrova_il_t(self):
        self.assertAlmostEqual(self.m['t'], 3.01, delta=0.1)


if __name__ == '__main__':
    unittest.main()
