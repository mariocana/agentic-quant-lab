"""Schema checks on quantlake tables.

The only contract between alphaquant and quantlake is the shape of the
tables. If quantlake changes it, alphaquant must stop with a message that
names the table and the column, never compute on wrong data.
"""
import polars as pl


class SchemaError(ValueError):
    """A quantlake table does not have the columns or types alphaquant expects."""


def require_columns(schema: pl.Schema, required: dict[str, pl.DataType], table: str) -> None:
    """Check presence and exact dtype of each required column; report every problem at once."""
    problems = []
    for name, expected in required.items():
        if name not in schema:
            problems.append(f"missing column '{name}'")
        elif schema[name] != expected:
            problems.append(f"column '{name}' is {schema[name]}, expected {expected}")
    if problems:
        raise SchemaError(f"{table}: " + "; ".join(problems))


def require_utc_datetime(schema: pl.Schema, column: str, table: str) -> None:
    """Any time unit is accepted, but the column must be a UTC-aware datetime."""
    dtype = schema.get(column)
    if dtype is None:
        raise SchemaError(f"{table}: missing column '{column}'")
    if not isinstance(dtype, pl.Datetime) or dtype.time_zone != "UTC":
        raise SchemaError(f"{table}: column '{column}' is {dtype}, expected Datetime with time_zone='UTC'")
