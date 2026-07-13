from types import SimpleNamespace

import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_datasource_csv.providers.profile_provider import (
    ProfileProvider,
    resolve_hk_uk_row,
)


def _building():
    return SimpleNamespace(hk_geb="HK", uk_geb="UK")


def _assignment(schedule_name="same_schedule"):
    return pd.DataFrame(
        [{"hk_geb": "HK", "uk_geb": "UK", "schedule_name": schedule_name}]
    )


def _schedule_file():
    return pd.DataFrame(
        [
            {"People": 1.0, "Appliances": 2.0},
            {"People": 3.0, "Appliances": 4.0},
        ]
    )


def test_profile_provider_schedule_cache_by_schedule_name():
    calls = []
    provider = ProfileProvider()

    def fake_schedule_reader(schedule_name):
        calls.append(schedule_name)
        return _schedule_file()

    first_entries, first_name, first_people_sum = provider.get_schedule(
        building=_building(),
        occupancy_schedules_assignments=_assignment("same_schedule"),
        schedule_reader=fake_schedule_reader,
    )
    second_entries, second_name, second_people_sum = provider.get_schedule(
        building=_building(),
        occupancy_schedules_assignments=_assignment("same_schedule"),
        schedule_reader=fake_schedule_reader,
    )

    assert calls == ["same_schedule"]
    assert first_name == "same_schedule"
    assert second_name == "same_schedule"
    assert first_people_sum == 4.0
    assert second_people_sum == 4.0
    assert first_entries is not second_entries
    assert first_entries[0] is second_entries[0]


def test_resolve_hk_uk_row_rejects_duplicate_matches():
    assignments = pd.DataFrame(
        [
            {"hk_geb": "HK", "uk_geb": "UK"},
            {"hk_geb": "HK", "uk_geb": "UK"},
        ]
    )

    with pytest.raises(DIBSInputError) as error_info:
        resolve_hk_uk_row(
            assignments,
            _building(),
            "datasource.test",
            "No row found",
        )

    assert error_info.value.phase == "datasource.test"
    assert error_info.value.context == {"hk_geb": "HK", "uk_geb": "UK", "matches": 2}


def test_profile_provider_rejects_unknown_gains_norm():
    provider = ProfileProvider()

    with pytest.raises(DIBSInputError) as error_info:
        provider.get_gains(
            building=_building(),
            profiles_zuweisungen_data=pd.DataFrame(
                [{"hk_geb": "HK", "uk_geb": "UK"}]
            ),
            profile_from_norm="unknown_norm",
            gains_from_group_values="low",
        )

    assert error_info.value.phase == "datasource.gains"
    assert error_info.value.context == {"profile_from_norm": "unknown_norm"}
