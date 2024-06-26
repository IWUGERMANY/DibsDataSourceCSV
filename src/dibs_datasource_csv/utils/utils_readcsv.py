"""
This file only contains methods that simply read different csv files
"""

import os
import pandas as pd
from dibs_data.data_utils import get_data_path


def read_user_building(data_path: str) -> pd.DataFrame | None:
    """
    This method reads the file which contains the building data to simulate.
    Args:
        data_path: where the file is located

    Returns:
        building
    Return type:
        Building
    """
    # path_parts = data_path.split("/")
    # file_path = os.path.join(*path_parts)

    return pd.read_csv(data_path, sep=";", index_col=False, encoding="utf8")


def read_user_buildings(data_path: str) -> pd.DataFrame | None:
    """
    This method reads the file which contains the building data to simulate.
    Args:
        data_path: where the file is located

    Returns:
        building
    Return type:
        Building
    """
    # path_parts = data_path.split("/")
    # file_path = os.path.join(*path_parts)

    return pd.read_csv(data_path, sep=";", index_col=False, encoding="utf8")


def read_gwp_pe_factors_data() -> pd.DataFrame | None:
    """
    Reads the csv file Primary_energy_and_emission_factors and replaces in the dataframe nan value with None
    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(
        data_path, "LCA", "Primary_energy_and_emission_factors.csv"
    )
    data = pd.read_csv(
        file_path,
        sep=";",
        decimal=",",
        index_col=False,
        encoding="cp1250",
    )
    nan_values = data[data["Energy Carrier"].isna()]
    if not nan_values.empty:
        data["Energy Carrier"].replace({pd.NaT: "None"}, inplace=True)
    return data


def read_plz_codes_data() -> pd.DataFrame | None:
    """
    Reads the csv file plzcodes
    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(data_path, "auxiliary", "weather_data", "plzcodes.csv")

    return pd.read_csv(
        file_path,
        encoding="latin",
        dtype={"zipcode": int},
    )


def read_profiles_zuweisungen_data() -> pd.DataFrame | None:
    """
    Reads the csv file profiles_zuweisungen
    Args:
        file_path: file to read

    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(
        data_path, "auxiliary", "norm_profiles", "profiles_zuweisungen.csv"
    )

    return pd.read_csv(file_path, sep=";", encoding="latin")


def read_occupancy_schedules_zuweisungen_data() -> pd.DataFrame | None:
    """
    Reads the csv file occupancy_schedules_zuweisungen
    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(
        data_path,
        "auxiliary",
        "occupancy_schedules",
        "occupancy_schedules_zuweisungen.csv",
    )

    return pd.read_csv(
        file_path,
        sep=";",
        encoding="latin",
    )


def read_schedule_file(schedule_name) -> pd.DataFrame | None:
    """
    Reads the csv file schedule_name
    Args:
        schedule_name:

    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(data_path, "auxiliary", "occupancy_schedules")
    file_name = schedule_name + ".csv"
    build_path = os.path.join(file_path, file_name)

    return pd.read_csv(
        build_path,
        sep=";",
    )


def read_weather_data(epwfile_path: str) -> pd.DataFrame | None:
    """
    Reads the csv file epwfile_path
    Args:
        epwfile_path:

    Returns:
        dataframe
    """
    return pd.read_csv(epwfile_path, skiprows=8, header=None)


def read_vergleichswerte_zuweisung() -> pd.DataFrame | None:
    """
    Reads the csv file TEK_NWG_Vergleichswerte_zuweisung
    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(
        data_path, "auxiliary", "TEKs", "TEK_NWG_Vergleichswerte_zuweisung.csv"
    )

    return pd.read_csv(
        file_path,
        sep=";",
        decimal=",",
        encoding="cp1250",
    )


def read_tek_nwg_comparative_values() -> pd.DataFrame | None:
    """
    Reads the csv file TEK_NWG_Vergleichswerte
    Returns:
        dataframe
    """
    data_path = get_data_path()
    file_path = os.path.join(
        data_path, "auxiliary", "TEKs", "TEK_NWG_Vergleichswerte.csv"
    )

    return pd.read_csv(
        file_path,
        sep=";",
        decimal=",",
        index_col=False,
        encoding="cp1250",
    )
