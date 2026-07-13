from types import SimpleNamespace

import pandas as pd

import dibs_datasource_csv.datasource_csv as datasource_module


def make_datasource(schedule_name="schedule_a"):
    datasource = datasource_module.DataSourceCSV.__new__(
        datasource_module.DataSourceCSV
    )
    datasource.building = SimpleNamespace(hk_geb="HK", uk_geb="UK")
    datasource.occupancy_schedules_assignments = pd.DataFrame(
        [{"hk_geb": "HK", "uk_geb": "UK", "schedule_name": schedule_name}]
    )
    datasource._schedule_cache = {}
    return datasource


def schedule_file():
    return pd.DataFrame(
        [
            {"People": 1.0, "Appliances": 2.0},
            {"People": 3.0, "Appliances": 4.0},
        ]
    )


def test_schedule_is_cached_by_schedule_name(monkeypatch):
    calls = []

    def fake_read_schedule_file(schedule_name):
        calls.append(schedule_name)
        return schedule_file()

    monkeypatch.setattr(datasource_module, "read_schedule_file", fake_read_schedule_file)

    datasource = make_datasource(schedule_name="same_schedule")

    first_entries, first_name, first_people_sum = datasource.get_schedule()
    second_entries, second_name, second_people_sum = datasource.get_schedule()

    assert calls == ["same_schedule"]
    assert first_name == "same_schedule"
    assert second_name == "same_schedule"
    assert first_people_sum == 4.0
    assert second_people_sum == 4.0
    assert first_entries is not second_entries
    assert first_entries[0] is second_entries[0]


def test_schedule_cache_uses_schedule_name_as_key(monkeypatch):
    calls = []

    def fake_read_schedule_file(schedule_name):
        calls.append(schedule_name)
        return schedule_file()

    monkeypatch.setattr(datasource_module, "read_schedule_file", fake_read_schedule_file)

    datasource = make_datasource(schedule_name="first_schedule")
    datasource.get_schedule()

    datasource.occupancy_schedules_assignments = pd.DataFrame(
        [{"hk_geb": "HK", "uk_geb": "UK", "schedule_name": "second_schedule"}]
    )
    datasource.get_schedule()

    assert calls == ["first_schedule", "second_schedule"]
