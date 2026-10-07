import polars as pl
from deltalake import DeltaTable

from helpers import minute_bars, utc
from quantlake import maintenance
from quantlake.bronze.ingest import add_partition_columns
from quantlake.storage import upsert


def _many_small_writes(path, n_writes: int = 6) -> pl.DataFrame:
    frames = []
    for i in range(n_writes):
        df = add_partition_columns(minute_bars(utc(2024, 1, 2, 9, i * 2), 2).drop("symbol"), "BTCUSDT")
        upsert(df, str(path))
        frames.append(df)
    return pl.concat(frames).sort("timestamp")


def _read(path) -> pl.DataFrame:
    return pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table()).sort("timestamp")


def test_find_tables_walks_nested_gold(tmp_path):
    _many_small_writes(tmp_path / "gold" / "strat" / "5m", 1)
    _many_small_writes(tmp_path / "gold" / "strat" / "1h", 1)
    (tmp_path / "gold" / "not_a_table").mkdir()
    assert maintenance.find_tables(tmp_path / "gold") == [
        tmp_path / "gold" / "strat" / "1h",
        tmp_path / "gold" / "strat" / "5m",
    ]
    assert maintenance.find_tables(tmp_path / "missing") == []


def test_compacts_and_vacuums_without_changing_data(tmp_path):
    path = tmp_path / "bronze" / "t"
    expected = _many_small_writes(path)
    before = len(DeltaTable(str(path)).file_uris())
    assert before == 6

    reports = maintenance.run(layers=("bronze",), retention_hours=0, data_root=tmp_path)
    (r,) = reports
    assert r.error is None
    assert r.files_removed == 6 and r.files_added == 1
    assert r.vacuumed == 6
    assert len(DeltaTable(str(path)).file_uris()) == 1
    assert len(list(path.rglob("*.parquet"))) == 1
    assert _read(path).equals(expected.select(_read(path).columns))


def test_dry_run_changes_nothing(tmp_path):
    path = tmp_path / "silver" / "t"
    _many_small_writes(path, 3)
    (r,) = maintenance.run(layers=("silver",), retention_hours=0, dry_run=True, data_root=tmp_path)
    assert r.files_before == 3 and r.files_added == 0
    assert len(DeltaTable(str(path)).file_uris()) == 3


def test_broken_table_is_reported_not_raised(tmp_path):
    good = tmp_path / "gold" / "a"
    _many_small_writes(good, 2)
    bad = tmp_path / "gold" / "b" / "_delta_log"
    bad.mkdir(parents=True)
    (bad / "00000000000000000000.json").write_text("not json")
    reports = {r.path.name: r for r in maintenance.run(layers=("gold",), retention_hours=0, data_root=tmp_path)}
    assert reports["a"].error is None
    assert reports["b"].error is not None


def test_gold_tables_read_by_alpha_quant_are_not_vacuumed(tmp_path, monkeypatch):
    import quantlake.reference.instruments as ref
    from quantlake.reference.instruments import DEFAULT_INSTRUMENTS, instruments_frame, upsert_instruments

    monkeypatch.setattr(ref, "REFERENCE_ROOT", tmp_path / "reference")
    upsert_instruments(instruments_frame([dict(DEFAULT_INSTRUMENTS[2])]))  # BTCUSDT → binance_spot_ohlcv
    assert maintenance.protected_gold_tables(tmp_path) == {"binance_spot_ohlcv"}

    kept = tmp_path / "gold" / "binance_spot_ohlcv" / "5m"
    other = tmp_path / "gold" / "some_strategy" / "5m"
    expected = _many_small_writes(kept, 3)
    _many_small_writes(other, 3)

    reports = {r.path: r for r in maintenance.run(layers=("gold",), retention_hours=0, data_root=tmp_path)}
    assert reports[kept].vacuum_skipped and reports[kept].vacuumed == 0
    assert reports[kept].files_added == 1  # still compacted
    assert len(list(kept.rglob("*.parquet"))) == 4  # old files kept on disk
    assert not reports[other].vacuum_skipped and reports[other].vacuumed == 3

    # every old version of the protected table is still readable
    for v in range(DeltaTable(str(kept)).version() + 1):
        DeltaTable(str(kept), version=v).to_pyarrow_table()
    assert _read(kept).equals(expected.select(_read(kept).columns))


def test_no_reference_table_protects_nothing(tmp_path):
    assert maintenance.protected_gold_tables(tmp_path) == set()
