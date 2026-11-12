"""Il registro vale qualcosa solo se non si può riscrivere in silenzio."""
import json

import pytest

from ricerca.registry import REGISTRY_PATH, Registry, RegistryError


@pytest.fixture
def r(tmp_path):
    return Registry(tmp_path / "t.jsonl")


def test_un_idea_conta_dalla_nascita_e_una_volta_sola(r):
    r.register_idea("fine_mese", "Flussi di fine mese sui futures su indice", "user", horizon="intraday", market="NQ")
    assert r.ideas() == ["fine_mese"]
    with pytest.raises(RegistryError):
        r.register_idea("fine_mese", "la stessa, con altre parole", "researcher")
    r.verify()


def test_una_variante_nomina_la_madre(r):
    with pytest.raises(RegistryError):
        r.register_idea("fine_mese_v2", "variante", "user", parent="fine_mese")
    r.register_idea("fine_mese", "madre", "user")
    r.register_idea("fine_mese_v2", "variante", "user", parent="fine_mese")
    assert r.ideas() == ["fine_mese", "fine_mese_v2"]


def test_un_idea_uccisa_resta_e_non_si_rimisura_ne_si_uccide_due_volte(r):
    r.register_idea("a", "idea a", "researcher")
    r.kill_idea("a", "critic", "nessuno che perde")
    assert "a" in r.ideas() and r.killed()["a"]["step"] == "critic"
    with pytest.raises(RegistryError):
        r.record_measure("a", {"eccesso_pp": 1.0})
    with pytest.raises(RegistryError):
        r.kill_idea("a", "user", "di nuovo")


def test_ogni_idea_misurata_conta_una_volta_qualunque_fine_faccia(r):
    for i in ("a", "b", "c"):
        r.register_idea(i, f"idea {i}", "user")
    r.record_measure("a", {"eccesso_pp": 2.6})
    r.record_measure("a", {"eccesso_pp": 2.6})          # rilancio dopo un bug: sempre un'idea
    r.record_measure("b", {"eccesso_pp": -0.6})
    r.kill_idea("b", "measure", "sotto soglia")
    r.kill_idea("c", "critic", "le fonti non lo dicono")
    assert r.ideas_measured() == 2


def test_porta_e_passo_sono_insiemi_chiusi(r):
    with pytest.raises(ValueError):
        r.register_idea("a", "idea", "corso")
    r.register_idea("a", "idea", "user")
    with pytest.raises(ValueError):
        r.kill_idea("a", "coder", "no")


def test_una_riga_modificata_rompe_la_catena(r):
    r.register_idea("a", "idea a", "user")
    r.register_idea("b", "idea b", "user")
    righe = r.path.read_text().splitlines()
    prima = json.loads(righe[0])
    prima["title"] = "un altro titolo"
    r.path.write_text("\n".join([json.dumps(prima, sort_keys=True), righe[1]]) + "\n")
    with pytest.raises(RegistryError):
        r.verify()
    with pytest.raises(RegistryError):
        r.register_idea("c", "non si allunga una catena rotta", "user")


def test_una_riga_tolta_rompe_la_catena(r):
    for i in ("a", "b", "c"):
        r.register_idea(i, f"idea {i}", "user")
    righe = r.path.read_text().splitlines()
    r.path.write_text("\n".join([righe[0], righe[2]]) + "\n")
    with pytest.raises(RegistryError):
        r.verify()


def test_il_registro_vero_ha_la_catena_intatta():
    """Le prime righe sono della fabbrica Hyperliquid chiusa il 12/11/2026: devono restare leggibili."""
    Registry(REGISTRY_PATH).verify()
