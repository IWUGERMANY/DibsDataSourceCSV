"""
This file only contains methods that simply read different csv files
"""

import os
from pathlib import Path

import pandas as pd
from pandas.errors import ParserError

from dibs_computing_core.iso_simulator.exceptions.base import DIBSDataSourceError
from dibs_data.data_utils import get_data_path


def _safe_read_csv(
    file_path: str,
    *,
    phase: str,
    file_type: str,
    context: dict | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Read a CSV file and translate parser/I/O failures to DIBSDataSourceError."""
    try:
        return pd.read_csv(file_path, **kwargs)
    except (FileNotFoundError, UnicodeDecodeError, ParserError, OSError) as error:
        error_context = {
            "file_type": file_type,
            "file_name": Path(file_path).name,
            **(context or {}),
            "error_type": type(error).__name__,
        }
        raise DIBSDataSourceError(
            f"Cannot read {file_type}",
            phase=phase,
            context=error_context,
        ) from error


def _read_dibs_data_csv(
    relative_parts: tuple[str, ...],
    *,
    phase: str,
    file_type: str,
    **kwargs,
) -> pd.DataFrame:
    """Read a CSV file located under the installed dibs_data package."""
    file_path = os.path.join(get_data_path(), *relative_parts)
    return _safe_read_csv(
        file_path,
        phase=phase,
        file_type=file_type,
        **kwargs,
    )


def _convert_numeric_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric-looking CSV columns while preserving text columns."""
    for column in dataframe.columns:
        try:
            dataframe[column] = pd.to_numeric(dataframe[column])
        except (TypeError, ValueError):
            # Non-numeric text columns such as system names must remain strings.
            pass
    return dataframe


def _read_user_buildings_csv(
    data_path: str,
    *,
    phase: str,
    file_type: str,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read user building CSV rows with DIBS-specific separators and decimals."""
    dataframe = _safe_read_csv(
        data_path,
        phase=phase,
        file_type=file_type,
        sep=";",
        index_col=False,
        encoding="utf-8",
        decimal=",",
        nrows=nrows,
    )
    return _convert_numeric_columns(dataframe)


def read_user_building(data_path: str) -> pd.DataFrame:
    """
    Read only the first building row from the user CSV.
    """
    return _read_user_buildings_csv(
        data_path,
        phase="datasource.user_building",
        file_type="user_building_csv",
        nrows=1,
    )


def read_user_buildings(data_path: str) -> pd.DataFrame:
    """
    Read all building rows from the user CSV.
    """
    return _read_user_buildings_csv(
        data_path,
        phase="datasource.user_buildings",
        file_type="user_buildings_csv",
    )


def read_gwp_pe_factors_data() -> pd.DataFrame:
    """
    Reads the csv file Primary_energy_and_emission_factors and replaces in the dataframe nan value with None
    Returns:
        dataframe
    """
    data = _read_dibs_data_csv(
        ("LCA", "Primary_energy_and_emission_factors.csv"),
        phase="datasource.primary_energy_factors",
        file_type="primary_energy_factors_csv",
        sep=";",
        decimal=",",
        index_col=False,
        encoding="utf-8",
    )
    if "Energy Carrier" in data.columns:
        data["Energy Carrier"] = data["Energy Carrier"].fillna("None")

    return data


def read_plz_codes_data() -> pd.DataFrame:
    """
    Reads the csv file plzcodes
    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "weather_data", "plzcodes.csv"),
        phase="datasource.plz_codes",
        file_type="plz_codes_csv",
        encoding="latin",
        dtype={"zipcode": int},
    )


def read_profiles_zuweisungen_data() -> pd.DataFrame:
    """
    Reads the csv file profiles_zuweisungen
    Args:
        file_path: file to read

    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "norm_profiles", "profiles_zuweisungen.csv"),
        phase="datasource.profiles_assignment",
        file_type="profiles_assignment_csv",
        sep=";",
        encoding="utf-8",
    )


def read_occupancy_schedules_zuweisungen_data() -> pd.DataFrame:
    """
    Reads the csv file occupancy_schedules_zuweisungen
    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "occupancy_schedules", "occupancy_schedules_zuweisungen.csv"),
        phase="datasource.schedule_assignment",
        file_type="schedule_assignment_csv",
        sep=";",
        encoding="utf-8",
    )


def read_schedule_file(schedule_name) -> pd.DataFrame:
    """
    Reads the csv file schedule_name
    Args:
        schedule_name:

    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "occupancy_schedules", schedule_name + ".csv"),
        phase="datasource.schedule_file",
        file_type="schedule_csv",
        sep=";",
    )


def read_weather_data(epwfile_path: str) -> pd.DataFrame:
    """
    Reads the csv file epwfile_path
    Args:
        epwfile_path:

    Returns:
        dataframe
    """
    return _safe_read_csv(
        epwfile_path,
        phase="datasource.weather_data",
        file_type="weather_epw",
        skiprows=8,
        header=None,
    )


def read_vergleichswerte_zuweisung() -> pd.DataFrame:
    """
    Reads the csv file TEK_NWG_Vergleichswerte_zuweisung
    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "TEKs", "TEK_NWG_Vergleichswerte_zuweisung.csv"),
        phase="datasource.tek_assignment",
        file_type="tek_assignment_csv",
        sep=";",
        decimal=",",
        encoding="utf-8",
        # encoding="cp1250",
    )


def read_tek_nwg_comparative_values() -> pd.DataFrame:
    """
    Reads the csv file TEK_NWG_Vergleichswerte
    Returns:
        dataframe
    """
    return _read_dibs_data_csv(
        ("auxiliary", "TEKs", "TEK_NWG_Vergleichswerte.csv"),
        phase="datasource.tek_values",
        file_type="tek_values_csv",
        sep=";",
        decimal=",",
        index_col=False,
        encoding="utf-8",
        # encoding="cp1250",
    )
