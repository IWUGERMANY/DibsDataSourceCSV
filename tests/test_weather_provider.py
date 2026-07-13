from types import SimpleNamespace

import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_datasource_csv.providers.weather_provider import WeatherProvider


def _weather_row():
    return pd.DataFrame([list(range(35))])


def _plz_data():
    return pd.DataFrame([{"zipcode": 12345, "latitude": 50.0, "longitude": 8.0}])


def _stations_data():
    return pd.DataFrame(
        [
            {"filename": "station_a.epw", "latitude": 50.1, "longitude": 8.1},
            {"filename": "station_b.epw", "latitude": 51.1, "longitude": 9.1},
        ]
    )


def test_weather_provider_caches_weather_data_by_period_and_file():
    calls = []
    provider = WeatherProvider("2004-2018")

    def fake_weather_reader(path):
        calls.append(path)
        return _weather_row()

    epw_file = SimpleNamespace(file_name="same.epw")
    first = provider.choose_weather_data_from_path(
        epw_file=epw_file,
        data_path_reader=lambda: "DATA_ROOT",
        weather_reader=fake_weather_reader,
    )
    second = provider.choose_weather_data_from_path(
        epw_file=epw_file,
        data_path_reader=lambda: "DATA_ROOT",
        weather_reader=fake_weather_reader,
    )

    assert len(calls) == 1
    assert first is not second
    assert first[0] is second[0]


def test_weather_provider_rejects_unknown_weather_period():
    provider = WeatherProvider("unknown")

    with pytest.raises(DIBSInputError) as error_info:
        provider.choose_weather_data_from_path(
            epw_file=SimpleNamespace(file_name="weather.epw"),
            data_path_reader=lambda: "DATA_ROOT",
            weather_reader=lambda path: _weather_row(),
        )

    assert error_info.value.phase == "datasource.weather_data"
    assert error_info.value.context == {"weather_period": "unknown"}


def test_weather_provider_caches_epw_file_by_period_and_plz():
    calls = {"stations": 0, "distance": 0}
    provider = WeatherProvider("2004-2018")

    def stations_reader(weather_period):
        calls["stations"] += 1
        return _stations_data()

    def distance_calculator(stations):
        calls["distance"] += 1
        stations["distance"] = [1.0, 2.0]

    building = SimpleNamespace(plz=12345)
    first = provider.get_epw_file(
        building=building,
        plz_codes_reader=_plz_data,
        stations_reader=stations_reader,
        distance_calculator=distance_calculator,
    )
    second = provider.get_epw_file(
        building=building,
        plz_codes_reader=_plz_data,
        stations_reader=stations_reader,
        distance_calculator=distance_calculator,
    )

    assert calls == {"stations": 1, "distance": 1}
    assert first.file_name == "station_a.epw"
    assert second.file_name == "station_a.epw"
    assert first is not second
