"""The raw market recorder. Its whole value is that it is there every hour without
fail, so these tests are about what happens when something goes wrong."""
from datetime import datetime, timezone

from desk.data import market_record as mr


class FakeInfo:
    """Two HIP-3 dexs; any name in `broken` fails like a builder endpoint that is down."""

    def __init__(self, broken=(), dex_list_fails=False):
        self.broken, self.dex_list_fails = set(broken), dex_list_fails

    def meta_and_asset_ctxs(self):
        return [{"universe": [{"name": "BTC"}, {"name": "UNI", "isDelisted": True}]},
                [{"markPx": "100"}, {"markPx": "5"}]]

    def post(self, path, body):
        if body["type"] == "perpDexs":
            if self.dex_list_fails:
                raise ConnectionError("perpDexs down")
            return [None, {"name": "xyz"}, {"name": "flx"}]
        if body["dex"] in self.broken:
            raise ConnectionError(f"{body['dex']} down")
        return [{"universe": [{"name": f"{body['dex']}:TSLA"}]}, [{"markPx": "250"}]]


T1 = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 11, 9, 11, 0, tzinfo=timezone.utc)


def test_samples_append_to_one_file_per_utc_day(tmp_path):
    p1 = mr.record(FakeInfo(), T1, root=tmp_path)
    p2 = mr.record(FakeInfo(), T2, root=tmp_path)
    p3 = mr.record(FakeInfo(), datetime(2026, 11, 10, 0, 5, tzinfo=timezone.utc), root=tmp_path)
    assert p1 == p2 and p1.name == "2026-11-09.jsonl.gz" and p3.name == "2026-11-10.jsonl.gz"

    rows = mr.read_day(p1)
    assert [r["ts"] for r in rows] == [T1.isoformat(), T2.isoformat()]
    assert [d["dex"] for d in rows[0]["dexs"]] == ["", "xyz", "flx"]


def test_delisted_assets_are_kept(tmp_path):
    """The delisting date exists only here: the flag flips and the API never says when."""
    rows = mr.read_day(mr.record(FakeInfo(), T1, root=tmp_path))
    names = {u["name"]: u for u in rows[0]["dexs"][0]["data"][0]["universe"]}
    assert names["UNI"]["isDelisted"] is True


def test_one_dex_down_does_not_cost_the_others(tmp_path):
    rows = mr.read_day(mr.record(FakeInfo(broken={"xyz"}), T1, root=tmp_path))
    assert [d["dex"] for d in rows[0]["dexs"]] == ["", "flx"]
    assert rows[0]["errors"][0]["dex"] == "xyz"


def test_the_main_dex_survives_a_missing_dex_list(tmp_path):
    rows = mr.read_day(mr.record(FakeInfo(dex_list_fails=True), T1, root=tmp_path))
    assert [d["dex"] for d in rows[0]["dexs"]] == [""]
    assert rows[0]["errors"][0]["dex"] == "*"


def test_a_crash_mid_write_loses_only_the_last_sample(tmp_path):
    path = mr.record(FakeInfo(), T1, root=tmp_path)
    mr.record(FakeInfo(), T2, root=tmp_path)
    whole = path.read_bytes()
    third = mr.record(FakeInfo(), datetime(2026, 11, 9, 12, tzinfo=timezone.utc), root=tmp_path).read_bytes()[len(whole):]
    path.write_bytes(whole + third[: len(third) // 2])          # the process died here
    assert len(mr.read_day(path)) == 2


def test_a_day_from_a_url_never_escapes_the_directory(tmp_path):
    mr.record(FakeInfo(), T1, root=tmp_path)
    assert mr.day_file("2026-11-09", root=tmp_path) is not None
    for bad in ("../../.env", "2026-11-09/../../x", "2026-11-09.jsonl.gz", "", "..%2F.env"):
        assert mr.day_file(bad, root=tmp_path) is None, bad
    assert [d["day"] for d in mr.days(root=tmp_path)] == ["2026-11-09"]
