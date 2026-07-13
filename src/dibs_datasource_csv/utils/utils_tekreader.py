import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError


def get_tek_name(row: pd.DataFrame) -> str:
    """Extract the TEK category name from a TEK assignment row."""
    return row["TEK"].astype(str).iloc[0]


def get_tek_data_frame_based_on_tek_name(
    DB_TEKs: pd.DataFrame, TEK_name: str
) -> pd.DataFrame:
    """Filter TEK comparative values to the selected TEK category."""
    tek_data = DB_TEKs[DB_TEKs["TEK_Category"] == TEK_name]
    if tek_data.empty:
        raise DIBSInputError(
            "No TEK comparative values found for category",
            phase="datasource.tek",
            context={"tek_name": TEK_name},
        )
    return tek_data


def get_tek_dhw(df_TEK: pd.DataFrame) -> float:
    """Return the domestic hot water TEK value for the selected category."""
    if df_TEK.empty:
        raise DIBSInputError(
            "Cannot read domestic hot water TEK from an empty data frame",
            phase="datasource.tek",
            context={"field": "TEK Warmwasser"},
        )
    return float(df_TEK.iloc[0]["TEK Warmwasser"])
