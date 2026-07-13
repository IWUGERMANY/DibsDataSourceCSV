from types import SimpleNamespace

import pandas as pd

import dibs_datasource_csv.datasource_csv as datasource_module


def make_datasource(plz=12345, weather_period="2004-2018"):
    datasource = datasource_module.DataSourceCSV.__new__(
        datasource_module.DataSourceCSV
    )
    datasource.weather_period = weather_period
    datasource.building = SimpleNamespace(plz=plz)
    datasource.epw_file = None
    datasource._epw_file_cache = {}
    datasource._weather_stations_cache = {}
    datasource._plz_codes_data = None
    return datasource


def plz_data():
    return pd.DataFrame(
        [
            {"zipcode": 12345, "latitude": 50.0, "longitude": 8.0},
            {"zipcode": 54321, "latitude": 51.0, "longitude": 9.0},
        ]
    )


def stations_data():
    return pd.DataFrame(
        [
            {"filename": "station_a.epw", "latitude": 50.1, "longitude": 8.1},
            {"filename": "station_b.epw", "latitude": 51.1, "longitude": 9.1},
        ]
    )


def patch_epw_helpers(monkeypatch, calls):
    monkeypatch.setattr(datasource_module, "read_plz_codes_data", lambda: plz_data())

    def fake_get_weather_files_stations(weather_period):
        calls["stations"] += 1
        return stations_data()

    def fake_calculate_minimum_distance_to_next_weather_station(stations):
        calls["distance"] += 1
        stations["distance"] = [1.0, 2.0]

    monkeypatch.setattr(
        datasource_module,
        "get_weather_files_stations",
        fake_get_weather_files_stations,
    )
    monkeypatch.setattr(
        datasource_module,
        "calculate_minimum_distance_to_next_weather_station",
        fake_calculate_minimum_distance_to_next_weather_station,
    )


def test_epw_file_is_cached_by_weather_period_and_plz(monkeypatch):
    calls = {"stations": 0, "distance": 0}
    patch_epw_helpers(monkeypatch, calls)
    datasource = make_datasource(plz=12345)

    datasource.get_epw_file()
    first_epw_file = datasource.epw_file
    datasource.get_epw_file()
    second_epw_file = datasource.epw_file

    assert calls == {"stations": 1, "distance": 1}
    assert first_epw_file.file_name == "station_a.epw"
    assert second_epw_file.file_name == "station_a.epw"
    assert first_epw_file is not second_epw_file


def test_epw_file_cache_uses_plz_in_key(monkeypatch):
    calls = {"stations": 0, "distance": 0}
    patch_epw_helpers(monkeypatch, calls)
    datasource = make_datasource(plz=12345)

    datasource.get_epw_file()
    datasource.building = SimpleNamespace(plz=54321)
    datasource.get_epw_file()

    assert calls == {"stations": 1, "distance": 2}
