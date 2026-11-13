"""Registro delle strategie del motore: serie, simbolo, valore del punto, costi del report MC."""
from .dpb import DPB
from .obo import OBO
from .prova_nq_first5 import PROVA_NQ_FIRST5
from .prova_vwap_fade import VwapFade

STRATEGIE = {
    'dpb': dict(classe=DPB, simbolo='NQ', tf=(5, 15), punto=20.0, comm_lato=7.5, riscaldamento=10),
    'obo': dict(classe=OBO, simbolo='NQ', tf=(15,), punto=20.0, comm_lato=7.5, riscaldamento=60),
    'prova_nq_first5': dict(classe=PROVA_NQ_FIRST5, simbolo='NQ', tf=(5,), punto=20.0, comm_lato=7.5,
                            riscaldamento=5),
    'prova_vwap_fade': dict(classe=VwapFade, simbolo='NQ', tf=(5, 1), punto=20.0, comm_lato=7.5,
                            riscaldamento=3),
}
