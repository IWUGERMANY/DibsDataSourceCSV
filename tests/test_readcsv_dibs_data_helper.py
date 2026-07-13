import os

import pandas as pd

from dibs_datasource_csv.utils import utils_readcsv


def test_dibs_data_reader_builds_package_relative_path(monkeypatch):
    calls = []

    monkeypatch.setattr(utils_readcsv, "get_data_path", lambda: "C:/dibs-data")

    def fake_safe_read_csv(file_path, *, phase, file_type, **kwargs):
        calls.append(
            {
                "file_path": file_path,
                "phase": phase,
                "file_type": file_type,
                "kwargs": kwargs,
            }
        )
        return pd.DataFrame()

    monkeypatch.setattr(utils_readcsv, "_safe_read_csv", fake_safe_read_csv)

    result = utils_readcsv.read_profiles_zuweisungen_data()

    assert isinstance(result, pd.DataFrame)
    assert calls == [
        {
            "file_path": os.path.join(
                "C:/dibs-data", "auxiliary", "norm_profiles", "profiles_zuweisungen.csv"
            ),
            "phase": "datasource.profiles_assignment",
            "file_type": "profiles_assignment_csv",
            "kwargs": {"sep": ";", "encoding": "utf-8"},
        }
    ]


def test_schedule_reader_uses_schedule_name_in_relative_path(monkeypatch):
    calls = []

    monkeypatch.setattr(utils_readcsv, "get_data_path", lambda: "C:/dibs-data")

    def fake_safe_read_csv(file_path, *, phase, file_type, **kwargs):
        calls.append((file_path, phase, file_type, kwargs))
        return pd.DataFrame()

    monkeypatch.setattr(utils_readcsv, "_safe_read_csv", fake_safe_read_csv)

    utils_readcsv.read_schedule_file("schedule_a")

    assert calls == [
        (
            os.path.join("C:/dibs-data", "auxiliary", "occupancy_schedules", "schedule_a.csv"),
            "datasource.schedule_file",
            "schedule_csv",
            {"sep": ";"},
        )
    ]


def test_direct_weather_reader_keeps_external_path(monkeypatch):
    calls = []

    def fake_safe_read_csv(file_path, *, phase, file_type, **kwargs):
        calls.append((file_path, phase, file_type, kwargs))
        return pd.DataFrame()

    monkeypatch.setattr(utils_readcsv, "_safe_read_csv", fake_safe_read_csv)

    utils_readcsv.read_weather_data("D:/weather/file.epw")

    assert calls == [
        (
            "D:/weather/file.epw",
            "datasource.weather_data",
            "weather_epw",
            {"skiprows": 8, "header": None},
        )
    ]
