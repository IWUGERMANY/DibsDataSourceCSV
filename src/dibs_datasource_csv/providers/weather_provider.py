"""Weather and EPW lookup provider for DataSourceCSV."""

import os

import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.model.epw_file import EPWFile
from dibs_computing_core.iso_simulator.model.weather_data import WeatherData
from dibs_data.data_utils import get_data_path

from ..utils.utils_epwfile import (
    calculate_minimum_distance_to_next_weather_station,
    get_coordinates_plz,
    get_coordinates_station,
    get_distance,
    get_filename_with_minimum_distance,
    get_weather_files_stations,
)
from ..utils.utils_readcsv import read_plz_codes_data, read_weather_data


class WeatherProvider:
    """Resolve EPW files and WeatherData rows for one DataSourceCSV instance."""

    def __init__(
        self,
        weather_period: str,
        weather_data_cache: dict | None = None,
        epw_file_cache: dict | None = None,
        weather_stations_cache: dict | None = None,
        plz_codes_data=None,
    ) -> None:
        self.weather_period = weather_period
        self.weather_data_cache = (
            weather_data_cache if weather_data_cache is not None else {}
        )
        self.epw_file_cache = epw_file_cache if epw_file_cache is not None else {}
        self.weather_stations_cache = (
            weather_stations_cache if weather_stations_cache is not None else {}
        )
        self.plz_codes_data = plz_codes_data

    def choose_weather_data_from_path(
        self,
        *,
        epw_file,
        data_path_reader=get_data_path,
        weather_reader=read_weather_data,
    ) -> list[WeatherData]:
        """Return WeatherData objects for the configured period and EPW file."""
        cache_key = (self.weather_period, epw_file.file_name)
        cached_weather_data = self.weather_data_cache.get(cache_key)
        if cached_weather_data is not None:
            return list(cached_weather_data)

        path_data = data_path_reader()
        if self.weather_period == "2007-2021":
            weather_path = os.path.join(
                path_data,
                "auxiliary",
                "weather_data_TMYx_2007_2021",
                epw_file.file_name,
            )
        elif self.weather_period == "2004-2018":
            weather_path = os.path.join(
                path_data, "auxiliary", "weather_data", epw_file.file_name
            )
        else:
            raise DIBSInputError(
                "Unsupported weather period",
                phase="datasource.weather_data",
                context={"weather_period": self.weather_period},
            )

        weather_data: pd.DataFrame = weather_reader(weather_path)
        weather_data_objects = tuple(
            WeatherData(*row.values) for _, row in weather_data.iterrows()
        )
        self.weather_data_cache[cache_key] = weather_data_objects
        return list(weather_data_objects)

    def get_epw_file(
        self,
        *,
        building,
        plz_codes_reader=read_plz_codes_data,
        stations_reader=get_weather_files_stations,
        coordinates_plz_reader=get_coordinates_plz,
        distance_calculator=calculate_minimum_distance_to_next_weather_station,
        filename_reader=get_filename_with_minimum_distance,
        coordinates_station_reader=get_coordinates_station,
        distance_reader=get_distance,
    ) -> EPWFile:
        """Return the closest EPW file for the building postcode."""
        cache_key = (self.weather_period, building.plz)
        cached_epw_file = self.epw_file_cache.get(cache_key)
        if cached_epw_file is not None:
            file_name, coordinates_station, distance = cached_epw_file
            return EPWFile(file_name, list(coordinates_station), distance)

        if self.plz_codes_data is None:
            self.plz_codes_data = plz_codes_reader()
        plz_data: pd.DataFrame = self.plz_codes_data

        weather_files_stations = self.weather_stations_cache.get(self.weather_period)
        if weather_files_stations is None:
            weather_files_stations = stations_reader(self.weather_period)
            self.weather_stations_cache[self.weather_period] = weather_files_stations

        # Work on a copy because distance and building coordinates are request-specific.
        weather_files_stations = weather_files_stations.copy()

        (
            weather_files_stations["latitude_building"],
            weather_files_stations["longitude_building"],
        ) = coordinates_plz_reader(plz_data, building.plz)

        distance_calculator(weather_files_stations)

        epw_filename: str = filename_reader(weather_files_stations)
        coordinates_station: list = coordinates_station_reader(weather_files_stations)
        distance: float = distance_reader(weather_files_stations)

        self.epw_file_cache[cache_key] = (
            epw_filename,
            tuple(coordinates_station),
            distance,
        )
        return EPWFile(epw_filename, coordinates_station, distance)
