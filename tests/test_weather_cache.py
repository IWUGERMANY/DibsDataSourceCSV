from types import SimpleNamespace

import pandas as pd

import dibs_datasource_csv.datasource_csv as datasource_module


def make_datasource(file_name="weather.epw", weather_period="2004-2018"):
    datasource = datasource_module.DataSourceCSV.__new__(
        datasource_module.DataSourceCSV
    )
    datasource.weather_period = weather_period
    datasource.epw_file = SimpleNamespace(file_name=file_name)
    datasource._weather_data_cache = {}
    return datasource


def one_weather_row():
    return pd.DataFrame([list(range(35))])


def test_weather_data_is_cached_by_period_and_epw_file(monkeypatch):
    calls = []

    def fake_read_weather_data(path):
        calls.append(path)
        return one_weather_row()

    monkeypatch.setattr(datasource_module, "get_data_path", lambda: "DATA_ROOT")
    monkeypatch.setattr(datasource_module, "read_weather_data", fake_read_weather_data)

    datasource = make_datasource(file_name="same.epw")

    first = datasource.choose_and_get_the_right_weather_data_from_path()
    second = datasource.choose_and_get_the_right_weather_data_from_path()

    assert len(calls) == 1
    assert len(first) == 1
    assert len(second) == 1
    assert first is not second
    assert first[0] is second[0]


def test_weather_data_cache_uses_epw_file_in_key(monkeypatch):
    calls = []

    def fake_read_weather_data(path):
        calls.append(path)
        return one_weather_row()

    monkeypatch.setattr(datasource_module, "get_data_path", lambda: "DATA_ROOT")
    monkeypatch.setattr(datasource_module, "read_weather_data", fake_read_weather_data)

    datasource = make_datasource(file_name="first.epw")
    datasource.choose_and_get_the_right_weather_data_from_path()

    datasource.epw_file = SimpleNamespace(file_name="second.epw")
    datasource.choose_and_get_the_right_weather_data_from_path()

    assert len(calls) == 2
