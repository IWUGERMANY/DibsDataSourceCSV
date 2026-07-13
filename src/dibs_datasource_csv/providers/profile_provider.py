"""Schedule, usage-time, and gains provider for DataSourceCSV."""

import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)
from dibs_computing_core.iso_simulator.exceptions.usage_time_exception import (
    UsageTimeError,
)
from dibs_computing_core.iso_simulator.model.schedule_name import ScheduleName

from ..utils.utils_hkgeb import find_hk_uk_rows
from ..utils.utils_normreader import (
    get_gain_per_person_and_appliance_and_typ_norm_18599,
    get_gain_per_person_and_appliance_and_typ_norm_mza,
    get_gain_per_person_and_appliance_and_typ_norm_sia2024,
    get_usage_start_end,
)
from ..utils.utils_readcsv import read_schedule_file
from ..utils.utils_schedule import get_schedule_name


def resolve_hk_uk_row(
    zuweisungen: pd.DataFrame,
    building,
    phase: str,
    not_found_message: str,
    not_found_error=HkOrUkNotFoundError,
) -> pd.DataFrame:
    """Resolve exactly one assignment row for the building HK/UK pair."""
    rows = find_hk_uk_rows(zuweisungen, building.hk_geb, building.uk_geb)
    context = {"hk_geb": building.hk_geb, "uk_geb": building.uk_geb}
    if rows.empty:
        raise not_found_error(
            not_found_message,
            phase=phase,
            context=context,
        )
    if len(rows) > 1:
        raise DIBSInputError(
            "Ambiguous building usage type mapping",
            phase=phase,
            context={**context, "matches": len(rows)},
        )
    return rows


class ProfileProvider:
    """Resolve profile-based schedule, usage-time, and gains data."""

    def __init__(self, schedule_cache: dict | None = None) -> None:
        self.schedule_cache = schedule_cache if schedule_cache is not None else {}

    def get_schedule(
        self,
        *,
        building,
        occupancy_schedules_assignments: pd.DataFrame,
        schedule_reader=read_schedule_file,
    ):
        """Return schedule entries, schedule name, and people sum for a building."""
        row = resolve_hk_uk_row(
            occupancy_schedules_assignments,
            building,
            "datasource.schedule",
            "No occupancy schedule found for building usage type",
        )
        schedule_name = get_schedule_name(row)
        cached_schedule = self.schedule_cache.get(schedule_name)
        if cached_schedule is None:
            schedule_file = schedule_reader(schedule_name)
            schedule_entries = tuple(
                ScheduleName(*row.values) for _, row in schedule_file.iterrows()
            )
            people_sum = schedule_file.People.sum()
            cached_schedule = (schedule_entries, people_sum)
            self.schedule_cache[schedule_name] = cached_schedule

        schedule_entries, people_sum = cached_schedule
        return list(schedule_entries), schedule_name, people_sum

    def get_usage_time(
        self,
        *,
        building,
        profiles_zuweisungen_data: pd.DataFrame,
        usage_from_norm: str,
    ):
        """Return usage start and end for the selected norm source."""
        row = resolve_hk_uk_row(
            profiles_zuweisungen_data,
            building,
            "datasource.usage_time",
            "No usage time found for building usage type",
            UsageTimeError,
        )
        return get_usage_start_end(str(usage_from_norm), row)

    def get_gains(
        self,
        *,
        building,
        profiles_zuweisungen_data: pd.DataFrame,
        profile_from_norm: str,
        gains_from_group_values: str,
    ):
        """Return person-gain tuple and appliance gains for the selected norm."""
        row = resolve_hk_uk_row(
            profiles_zuweisungen_data,
            building,
            "datasource.gains",
            "No gains profile found for building usage type",
        )

        if profile_from_norm == "sia2024":
            return get_gain_per_person_and_appliance_and_typ_norm_sia2024(
                row, gains_from_group_values
            )
        if profile_from_norm == "din18599":
            return get_gain_per_person_and_appliance_and_typ_norm_18599(
                row, gains_from_group_values
            )
        if profile_from_norm == "mza":
            return get_gain_per_person_and_appliance_and_typ_norm_mza(
                row, gains_from_group_values
            )

        raise DIBSInputError(
            "Unsupported gains profile norm",
            phase="datasource.gains",
            context={"profile_from_norm": profile_from_norm},
        )
