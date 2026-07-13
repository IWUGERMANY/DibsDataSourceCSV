"""Building CSV column validation and Building object mapping."""

from inspect import signature

import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.model.building import Building


EXPECTED_BUILDING_COLUMNS = tuple(
    name for name in signature(Building.__init__).parameters if name != "self"
)


def _duplicate_columns(columns) -> list[str]:
    """Return duplicate column names while preserving their first duplicate order."""
    seen = set()
    duplicates = []
    for column in columns:
        if column in seen and column not in duplicates:
            duplicates.append(column)
        seen.add(column)
    return duplicates


def prepare_building_dataframe(building_data: pd.DataFrame, phase: str) -> pd.DataFrame:
    """Validate and reorder building CSV columns to match the Core Building constructor."""
    columns = list(building_data.columns)
    missing_columns = [
        column for column in EXPECTED_BUILDING_COLUMNS if column not in columns
    ]
    extra_columns = [
        column for column in columns if column not in EXPECTED_BUILDING_COLUMNS
    ]
    duplicate_columns = _duplicate_columns(columns)

    if missing_columns or extra_columns or duplicate_columns:
        raise DIBSInputError(
            "Invalid building CSV columns",
            phase=phase,
            context={
                "missing_columns": missing_columns,
                "extra_columns": extra_columns,
                "duplicate_columns": duplicate_columns,
            },
        )

    return building_data.loc[:, EXPECTED_BUILDING_COLUMNS]


def build_building_from_row(row: pd.Series, building_class=Building) -> Building:
    """Create a Building object from a validated CSV row by explicit column name."""
    return building_class(*(row[column] for column in EXPECTED_BUILDING_COLUMNS))
