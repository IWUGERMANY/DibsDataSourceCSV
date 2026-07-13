from types import SimpleNamespace

import pandas as pd
import pytest

import dibs_datasource_csv.datasource_csv as datasource_module
from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)
from dibs_computing_core.iso_simulator.exceptions.usage_time_exception import (
    UsageTimeError,
)


def make_datasource(**overrides):
    datasource = datasource_module.DataSourceCSV.__new__(
        datasource_module.DataSourceCSV
    )
    defaults = {
        "building": SimpleNamespace(hk_geb="HK", uk_geb="UK"),
        "occupancy_schedules_assignments": pd.DataFrame(),
        "vergleichswerte_zuweisung": pd.DataFrame(),
        "tek_nwg_comparative_values": pd.DataFrame(),
        "profiles_zuweisungen_data": pd.DataFrame(),
        "profile_from_norm": "din18599",
        "gains_from_group_values": "mid",
        "usage_from_norm": "sia2024",
        "weather_period": "2004-2018",
        "primary_energy_factor": "GEG",
        "epw_file": SimpleNamespace(file_name="weather.epw"),
    }
    defaults.update(overrides)
    for name, value in defaults.items():
        setattr(datasource, name, value)
    return datasource


def usage_pair_table(rows=None):
    if rows is None:
        rows = [{"hk_geb": "HK", "uk_geb": "UK"}]
    return pd.DataFrame(rows)


def mismatched_usage_pair_table():
    return pd.DataFrame(
        [
            {"hk_geb": "HK", "uk_geb": "OTHER"},
            {"hk_geb": "OTHER", "uk_geb": "UK"},
        ]
    )


def test_get_schedule_rejects_mismatched_hk_uk_pair():
    datasource = make_datasource(
        occupancy_schedules_assignments=mismatched_usage_pair_table()
    )

    with pytest.raises(HkOrUkNotFoundError) as caught:
        datasource.get_schedule()

    assert caught.value.phase == "datasource.schedule"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK"}


def test_get_tek_rejects_mismatched_hk_uk_pair():
    datasource = make_datasource(
        vergleichswerte_zuweisung=mismatched_usage_pair_table()
    )

    with pytest.raises(HkOrUkNotFoundError) as caught:
        datasource.get_tek()

    assert caught.value.phase == "datasource.tek"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK"}


def test_get_usage_time_rejects_mismatched_hk_uk_pair():
    datasource = make_datasource(
        profiles_zuweisungen_data=mismatched_usage_pair_table()
    )

    with pytest.raises(UsageTimeError) as caught:
        datasource.get_usage_time()

    assert caught.value.phase == "datasource.usage_time"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK"}


def test_duplicate_hk_uk_pair_is_reported_as_ambiguous_mapping():
    datasource = make_datasource()
    duplicate_rows = usage_pair_table(
        [
            {"hk_geb": "HK", "uk_geb": "UK"},
            {"hk_geb": "HK", "uk_geb": "UK"},
        ]
    )

    with pytest.raises(DIBSInputError) as caught:
        datasource._resolve_hk_uk_row(
            duplicate_rows,
            "datasource.test",
            "No mapping found",
        )

    assert caught.value.phase == "datasource.test"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK", "matches": 2}


def test_get_gains_rejects_unknown_profile_norm():
    datasource = make_datasource(
        profile_from_norm="unknown",
        profiles_zuweisungen_data=usage_pair_table(),
    )

    with pytest.raises(DIBSInputError) as caught:
        datasource.get_gains()

    assert caught.value.phase == "datasource.gains"
    assert caught.value.context == {"profile_from_norm": "unknown"}


def test_get_epw_pe_factors_rejects_unknown_factor():
    datasource = make_datasource(primary_energy_factor="unknown")

    with pytest.raises(DIBSInputError) as caught:
        datasource.get_epw_pe_factors()

    assert caught.value.phase == "datasource.primary_energy_factors"


def test_weather_reader_rejects_unknown_period():
    datasource = make_datasource(weather_period="unknown")

    with pytest.raises(DIBSInputError) as caught:
        datasource.choose_and_get_the_right_weather_data_from_path()

    assert caught.value.phase == "datasource.weather_data"
