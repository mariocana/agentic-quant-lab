from datetime import datetime

import pytest


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
