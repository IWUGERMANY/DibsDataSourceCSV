"""TEK mapping provider for DataSourceCSV."""

import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)

from ..utils.utils_hkgeb import find_hk_uk_rows
from ..utils.utils_tekreader import (
    get_tek_data_frame_based_on_tek_name,
    get_tek_dhw,
    get_tek_name,
)


def resolve_tek_assignment_row(
    vergleichswerte_zuweisung: pd.DataFrame, building
) -> pd.DataFrame:
    """Resolve exactly one TEK assignment row for the building HK/UK pair."""
    rows = find_hk_uk_rows(
        vergleichswerte_zuweisung, building.hk_geb, building.uk_geb
    )
    context = {"hk_geb": building.hk_geb, "uk_geb": building.uk_geb}
    if rows.empty:
        raise HkOrUkNotFoundError(
            "No TEK value found for building usage type",
            phase="datasource.tek",
            context=context,
        )
    if len(rows) > 1:
        raise DIBSInputError(
            "Ambiguous building usage type mapping",
            phase="datasource.tek",
            context={**context, "matches": len(rows)},
        )
    return rows


def get_tek(
    *,
    vergleichswerte_zuweisung: pd.DataFrame,
    tek_nwg_comparative_values: pd.DataFrame,
    building,
) -> tuple[float, str]:
    """Return domestic hot-water TEK value and TEK category for a building."""
    row = resolve_tek_assignment_row(vergleichswerte_zuweisung, building)
    tek_name = get_tek_name(row)
    df_tek = get_tek_data_frame_based_on_tek_name(
        tek_nwg_comparative_values, tek_name
    )
    return get_tek_dhw(df_tek), tek_name
