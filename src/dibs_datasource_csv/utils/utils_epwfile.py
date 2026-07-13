import os

import pandas as pd
from geopy.distance import geodesic

from dibs_computing_core.iso_simulator.exceptions.plz_exception import PLZNotFoundError
from dibs_data.data_utils import get_data_path
from .utils_readcsv import _safe_read_csv


_MIN_DISTANCE_INDEX_ATTR = "dibs_min_distance_index"


def get_weather_files_stations(weather_period: str) -> pd.DataFrame:
    """Load the weather-station table for the selected weather period."""
    path_data = get_data_path()
    if weather_period == "2007-2021":
        file_path = os.path.join(
            path_data,
            "auxiliary",
            "weather_data_TMYx_2007_2021",
            "weatherfiles_stations_109.csv",
        )
    else:
        file_path = os.path.join(
            path_data, "auxiliary", "weather_data", "weatherfiles_stations_93.csv"
        )
    return _safe_read_csv(
        file_path,
        phase="datasource.epw_file",
        file_type="weather_station_csv",
        context={"weather_period": weather_period},
        sep=";",
    )


def get_coordinates_plz(plz_data: pd.DataFrame, plz: str) -> list[float]:
    """Return latitude and longitude for a postcode from the PLZ lookup table."""
    matches = plz_data.loc[plz_data["zipcode"] == plz, ["latitude", "longitude"]]
    if matches.empty:
        raise PLZNotFoundError(
            "Postcode could not be resolved",
            phase="datasource.epw_file",
            context={"plz": plz},
        )
    return matches.iloc[0].tolist()


def calculate_minimum_distance_to_next_weather_station(
    weatherfiles_stations: pd.DataFrame,
) -> None:
    """Add geodesic distance from the building to each weather station."""
    weatherfiles_stations.attrs.pop(_MIN_DISTANCE_INDEX_ATTR, None)
    weatherfiles_stations["distance"] = [
        geodesic((latitude, longitude), (latitude_building, longitude_building)).km
        for latitude, longitude, latitude_building, longitude_building in zip(
            weatherfiles_stations["latitude"],
            weatherfiles_stations["longitude"],
            weatherfiles_stations["latitude_building"],
            weatherfiles_stations["longitude_building"],
        )
    ]


def _get_minimum_distance_index(weatherfiles_stations: pd.DataFrame):
    """Return and cache the DataFrame index of the closest weather station."""
    minimum_distance_index = weatherfiles_stations.attrs.get(_MIN_DISTANCE_INDEX_ATTR)
    if minimum_distance_index is None:
        minimum_distance_index = weatherfiles_stations["distance"].idxmin()
        weatherfiles_stations.attrs[_MIN_DISTANCE_INDEX_ATTR] = minimum_distance_index
    return minimum_distance_index


def get_filename_with_minimum_distance(weatherfiles_stations: pd.DataFrame) -> str:
    """Return the EPW filename of the closest weather station."""
    return weatherfiles_stations.loc[
        _get_minimum_distance_index(weatherfiles_stations), "filename"
    ]


def get_coordinates_station(weatherfiles_stations: pd.DataFrame) -> list[float]:
    """Return coordinates of the closest weather station."""
    return weatherfiles_stations.loc[
        _get_minimum_distance_index(weatherfiles_stations), ["latitude", "longitude"]
    ].tolist()


def get_distance(weatherfiles_stations: pd.DataFrame) -> float:
    """Return the distance in kilometers to the closest weather station."""
    return weatherfiles_stations.loc[
        _get_minimum_distance_index(weatherfiles_stations), "distance"
    ]
