from deltalake import DeltaTable
import polars as pl
import pytest

from alphaquant.data.schema import SchemaError
from alphaquant.instruments import (
    AssetClass,
    ExchangeSession,
    PercentFee,
    PerContractFee,
    QuantlakeInstrumentSource,
    load_costs,
)

from conftest import reference_rows, write_delta


def test_fees():
    assert PerContractFee(per_side=2.5).fee(qty=-3, price=5000, multiplier=50) == 7.5
    pct = PercentFee(maker=0.0002, taker=0.001)
    assert pct.fee(qty=0.5, price=60_000, multiplier=1) == pytest.approx(30.0)
    assert pct.fee(qty=0.5, price=60_000, multiplier=1, liquidity="maker") == pytest.approx(6.0)


def test_load_costs_default_file_and_errors(tmp_path):
    costs = load_costs()
    assert costs["ES"].fee == PerContractFee(per_side=2.5)
    assert costs["BTCUSDT"].verified is False
    assert costs["BTCUSDT-PERP"].fee == PercentFee(maker=0.0002, taker=0.0005)

    bad = tmp_path / "costs.yaml"
    bad.write_text("profiles:\n  default:\n    ES: {fee: flat}\n")
    with pytest.raises(ValueError, match="unknown fee type"):
        load_costs(bad)
    with pytest.raises(KeyError, match="pessimistic"):
        load_costs(bad, profile="pessimistic")


def test_source_builds_instruments(data_root, costs):
    source = QuantlakeInstrumentSource(data_root, costs=costs)
    assert source.symbols() == ["BTCUSDT", "ES"]
    assert source.version == 0

    es = source.get("ES")
    assert es.asset_class is AssetClass.FUTURE
    assert es.multiplier == 50.0
    assert es.slippage == 0.25
    assert isinstance(es.session, ExchangeSession)
    assert es.data.gold_table == "multicharts_ohlcv" and es.data.symbol == "ES"

    btc = source.get("BTCUSDT")
    assert btc.session.name == "24/7"


def test_rounding(data_root, costs):
    source = QuantlakeInstrumentSource(data_root, costs=costs)
    es, btc = source.get("ES"), source.get("BTCUSDT")
    assert es.round_qty(2.9) == 2.0
    assert es.round_qty(-0.4) == 0.0
    assert btc.round_qty(0.123456789) == pytest.approx(0.12345)
    assert es.round_price(5000.13) == 5000.25
    assert es.round_price(5000.12) == 5000.0


def test_source_errors(data_root, costs):
    source = QuantlakeInstrumentSource(data_root, costs=costs)
    with pytest.raises(KeyError, match="not in reference/instruments"):
        source.get("NQ")
    with pytest.raises(KeyError, match="costs.yaml"):
        QuantlakeInstrumentSource(data_root, costs={"ES": costs["ES"]}).get("BTCUSDT")
    with pytest.raises(FileNotFoundError, match="reference/instruments"):
        QuantlakeInstrumentSource(data_root / "missing", costs=costs)


def test_source_schema_checks(tmp_path, costs):
    write_delta(reference_rows().drop("tick_size"), tmp_path / "reference" / "instruments")
    with pytest.raises(SchemaError, match="missing column 'tick_size'"):
        QuantlakeInstrumentSource(tmp_path, costs=costs)

    write_delta(pl.concat([reference_rows(), reference_rows().head(1)]), tmp_path / "reference" / "instruments")
    with pytest.raises(SchemaError, match="duplicated symbols"):
        QuantlakeInstrumentSource(tmp_path, costs=costs)


def test_source_reads_pinned_version(data_root, costs):
    path = data_root / "reference" / "instruments"
    write_delta(reference_rows().with_columns(pl.lit(0.5).alias("tick_size")), path)
    assert DeltaTable(str(path)).version() == 1

    assert QuantlakeInstrumentSource(data_root, costs=costs).get("ES").tick_size == 0.5
    pinned = QuantlakeInstrumentSource(data_root, costs=costs, version=0)
    assert pinned.version == 0 and pinned.get("ES").tick_size == 0.25


def test_hyperliquid_venue_costs_come_from_real_fills():
    from alphaquant.instruments.fees import load_venue_costs

    hl = load_venue_costs("hyperliquid")
    assert (hl.fee.maker, hl.fee.taker) == (0.00015, 0.00045)
    assert hl.fee_verified and not hl.slippage_verified, "testnet slippage is not mainnet slippage"
    assert hl.round_trip_bps("maker") == pytest.approx(3.0)
    assert hl.round_trip_bps("taker") == pytest.approx(2 * (4.5 + 7.3))
    hip3 = load_venue_costs("hyperliquid_hip3")
    assert not hip3.fee_verified and hip3.round_trip_bps("taker") > hl.round_trip_bps("taker")


def test_an_unknown_venue_is_an_error_not_a_zero():
    from alphaquant.instruments.fees import load_venue_costs

    with pytest.raises(KeyError):
        load_venue_costs("binance")
