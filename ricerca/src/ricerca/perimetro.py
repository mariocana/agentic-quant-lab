"""The research desk's perimeter: ricerca/perimetro.yaml, read by agents and enforced here.

What an agent is told in a prompt is a request; what this module refuses is a wall. So the
parts of the perimeter that can be checked are checked in code: which horizons are open,
which markets have data, how many new ideas may reach the measure in a month, and whether a
measure clears the floor that is the same for every idea.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

PERIMETRO_PATH = Path(__file__).resolve().parents[2] / "perimetro.yaml"


class Horizon(BaseModel):
    attivo: bool
    cosa: str
    flat_a_fine_giornata: bool
    segnali_al_giorno_min: float = Field(ge=0)
    misura: str | None = None


class Market(BaseModel):
    dati: bool


class MeasureRules(BaseModel):
    periodo: tuple[str, str]
    errori_standard_min: float = Field(gt=0)
    dollari_al_giorno_per_micro_min: float = Field(ge=0)
    idee_al_mese_max: int = Field(ge=1)


class Perimeter(BaseModel):
    orizzonti: dict[str, Horizon]
    mercati: dict[str, Market]
    misura: MeasureRules

    def check_idea(self, horizon: str, market: str) -> list[str]:
        """Why this idea is outside the perimeter; empty when it is inside."""
        out = []
        h = self.orizzonti.get(horizon)
        if h is None:
            out.append(f"orizzonte {horizon!r} sconosciuto: {sorted(self.orizzonti)}")
        elif not h.attivo:
            out.append(f"orizzonte {horizon!r} spento in perimetro.yaml")
        elif h.misura is None:
            out.append(f"orizzonte {horizon!r} acceso ma senza una misura: non si puo giudicare")
        m = self.mercati.get(market)
        if m is None:
            out.append(f"mercato {market!r} non in perimetro.yaml: {sorted(self.mercati)}")
        elif not m.dati:
            out.append(f"mercato {market!r}: mancano i dati nel lake")
        return out

    def check_measure(self, metrics: dict) -> list[str]:
        """Which floors the measure misses; empty when it clears them all."""
        r, out = self.misura, []
        es = metrics.get("errori_standard")
        if es is None or es < r.errori_standard_min:
            out.append(f"errori standard {es if es is None else round(es, 2)} < {r.errori_standard_min}")
        d = metrics.get("dollari_al_giorno_per_micro")
        if d is None or d < r.dollari_al_giorno_per_micro_min:
            out.append(f"$ al giorno per micro {d if d is None else round(d, 2)} < {r.dollari_al_giorno_per_micro_min}")
        return out


def load_perimeter(path: Path | None = None) -> Perimeter:
    return Perimeter.model_validate(yaml.safe_load(Path(path or PERIMETRO_PATH).read_text()))


def this_month(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m")
