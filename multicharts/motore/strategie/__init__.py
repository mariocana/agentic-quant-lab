"""Registro delle strategie del motore: serie, simbolo, valore del punto, costi del report MC."""
from .dpb import DPB

STRATEGIE = {
    'dpb': dict(classe=DPB, simbolo='NQ', tf=(5, 15), punto=20.0, comm_lato=7.5, riscaldamento=10),
}
