from datetime import datetime

import pytest

import quantlake.bronze.ingest as bronze
import quantlake.gold.ingest as gold
import quantlake.live as live
import quantlake.silver.ingest as silver


@pytest.fixture
def freeze_now(monkeypatch):
    """Freeze datetime.now(...) inside a module that did `from datetime import datetime`."""
    def _freeze(module, now: datetime):
        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return now if tz is None else now.astimezone(tz)

        monkeypatch.setattr(module, "datetime", FrozenDatetime)
    return _freeze


@pytest.fixture
def lake(tmp_path, monkeypatch):
    roots = {"BRONZE_ROOT": tmp_path / "bronze", "SILVER_ROOT": tmp_path / "silver", "GOLD_ROOT": tmp_path / "gold"}
    for mod in (bronze, silver, gold, live):
        for name, path in roots.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, path)
    return roots
