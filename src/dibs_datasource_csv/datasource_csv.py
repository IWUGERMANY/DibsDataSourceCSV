"""CSV DataSource facade for DibsComputingCore simulations."""

import pandas as pd

from dibs_computing_core.iso_simulator.data_source.datasource import DataSource

from .utils.utils_readcsv import (
    read_occupancy_schedules_zuweisungen_data,
    read_schedule_file,
    read_vergleichswerte_zuweisung,
    read_tek_nwg_comparative_values,
    read_weather_data,
    read_plz_codes_data,
    read_profiles_zuweisungen_data,
    read_user_building,
    read_user_buildings,
)
from .datasource_options import validate_datasource_options
from .providers.factor_provider import get_epw_pe_factors as load_epw_pe_factors
from .providers.tek_provider import get_tek as load_tek
from .providers.profile_provider import ProfileProvider, resolve_hk_uk_row
from .providers.weather_provider import WeatherProvider
from .building_mapper import (
    EXPECTED_BUILDING_COLUMNS,
    build_building_from_row,
    prepare_building_dataframe,
)

from dibs_computing_core.iso_simulator.model.building import Building
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)
from dibs_data.data_utils import get_data_path
from .utils.utils_epwfile import (
    calculate_minimum_distance_to_next_weather_station,
    get_coordinates_plz,
    get_coordinates_station,
    get_distance,
    get_filename_with_minimum_distance,
    get_weather_files_stations,
)

# Re-exported for compatibility with older tests and callers.
__all__ = ["DataSourceCSV", "EXPECTED_BUILDING_COLUMNS"]


class DataSourceCSV(DataSource):
    """CSV-backed DataSource implementation used by DIBS simulations.

    The class keeps the DataSource interface expected by DibsComputingCore and
    translates CSV/reference-table data into Core model objects. It owns small
    per-instance caches for immutable reference lookups such as schedules, EPW
    metadata, and weather files.
    """

    def __init__(
        self,
        data_path: str,
        profile_from_norm: str,
        gains_from_group_values: str,
        usage_from_norm: str,
        weather_period: str,
        primary_energy_factor: str,
    ):
        """Initialize options, static tables, result state, and providers."""
        validate_datasource_options(
            profile_from_norm=profile_from_norm,
            gains_from_group_values=gains_from_group_values,
            usage_from_norm=usage_from_norm,
            weather_period=weather_period,
            primary_energy_factor=primary_energy_factor,
        )
        self._set_options(
            data_path=data_path,
            profile_from_norm=profile_from_norm,
            gains_from_group_values=gains_from_group_values,
            usage_from_norm=usage_from_norm,
            weather_period=weather_period,
            primary_energy_factor=primary_energy_factor,
        )
        self._init_result_state()
        self._load_static_assignment_tables()
        self._init_providers()

    def _set_options(
        self,
        *,
        data_path: str,
        profile_from_norm: str,
        gains_from_group_values: str,
        usage_from_norm: str,
        weather_period: str,
        primary_energy_factor: str,
    ) -> None:
        """Store constructor options after validation."""
        self.data_path = data_path
        self.profile_from_norm = profile_from_norm
        self.gains_from_group_values = gains_from_group_values
        self.usage_from_norm = usage_from_norm
        self.weather_period = weather_period
        self.primary_energy_factor = primary_energy_factor

    def _init_result_state(self) -> None:
        """Initialize mutable simulation state populated by DataSource methods."""
        self.epw_file = None
        self.epw_pe_factors = None
        self.building = None
        self.buildings = None

    def _load_static_assignment_tables(self) -> None:
        """Load static CSV assignment tables used by provider methods."""
        self.occupancy_schedules_assignments = read_occupancy_schedules_zuweisungen_data()
        self.vergleichswerte_zuweisung = read_vergleichswerte_zuweisung()
        self.tek_nwg_comparative_values = read_tek_nwg_comparative_values()
        self.profiles_zuweisungen_data = read_profiles_zuweisungen_data()

    def _init_providers(self) -> None:
        """Initialize provider instances and the caches they own."""
        self._weather_data_cache = {}
        self._schedule_cache = {}
        self.profile_provider = ProfileProvider(self._schedule_cache)
        self._profile_provider = self.profile_provider
        self._epw_file_cache = {}
        self._weather_stations_cache = {}
        self._plz_codes_data = None
        self.weather_provider = WeatherProvider(
            self.weather_period,
            self._weather_data_cache,
            self._epw_file_cache,
            self._weather_stations_cache,
            self._plz_codes_data,
        )
        self._weather_provider = self.weather_provider

    def _get_profile_provider(self) -> ProfileProvider:
        """Return the profile provider, creating it for tests using __new__ if needed."""
        if not hasattr(self, "profile_provider"):
            self._schedule_cache = getattr(self, "_schedule_cache", {})
            self.profile_provider = ProfileProvider(self._schedule_cache)
            self._profile_provider = self.profile_provider
        return self.profile_provider

    def _get_weather_provider(self) -> WeatherProvider:
        """Return the weather provider, creating it for tests using __new__ if needed."""
        if not hasattr(self, "weather_provider"):
            self._weather_data_cache = getattr(self, "_weather_data_cache", {})
            self._epw_file_cache = getattr(self, "_epw_file_cache", {})
            self._weather_stations_cache = getattr(self, "_weather_stations_cache", {})
            self._plz_codes_data = getattr(self, "_plz_codes_data", None)
            self.weather_provider = WeatherProvider(
                self.weather_period,
                self._weather_data_cache,
                self._epw_file_cache,
                self._weather_stations_cache,
                self._plz_codes_data,
            )
            self._weather_provider = self.weather_provider
        return self.weather_provider

    def _resolve_hk_uk_row(
        self,
        zuweisungen: pd.DataFrame,
        phase: str,
        not_found_message: str,
        not_found_error=HkOrUkNotFoundError,
    ) -> pd.DataFrame:
        """Resolve exactly one assignment row for the current building's HK/UK pair."""
        return resolve_hk_uk_row(
            zuweisungen,
            self.building,
            phase,
            not_found_message,
            not_found_error,
        )

    def get_user_building(self):
        """Read one building from the configured input CSV."""
        building_data: pd.DataFrame = prepare_building_dataframe(
            read_user_building(self.data_path), "datasource.user_building"
        )
        self.building = build_building_from_row(building_data.iloc[0], Building)

    def get_user_buildings(self):
        """Read all buildings from the configured input CSV."""
        building_data: pd.DataFrame = prepare_building_dataframe(
            read_user_buildings(self.data_path), "datasource.user_buildings"
        )
        self.buildings = [
            build_building_from_row(row, Building) for _, row in building_data.iterrows()
        ]

    def get_epw_pe_factors(self):
        """Load primary-energy and emission factors for the configured factor source."""
        self.epw_pe_factors = load_epw_pe_factors(self.primary_energy_factor)

    def get_schedule(self):
        """Return the occupancy schedule tuple required by DibsComputingCore."""
        return self._get_profile_provider().get_schedule(
            building=self.building,
            occupancy_schedules_assignments=self.occupancy_schedules_assignments,
            schedule_reader=read_schedule_file,
        )

    def get_tek(self):
        """Return the TEK DHW value and TEK category for the current building."""
        return load_tek(
            vergleichswerte_zuweisung=self.vergleichswerte_zuweisung,
            tek_nwg_comparative_values=self.tek_nwg_comparative_values,
            building=self.building,
        )

    def choose_and_get_the_right_weather_data_from_path(self):
        """Return WeatherData rows for the selected weather period and EPW file."""
        return self._get_weather_provider().choose_weather_data_from_path(
            epw_file=self.epw_file,
            data_path_reader=get_data_path,
            weather_reader=read_weather_data,
        )

    def get_epw_file(self):
        """Resolve and store the closest EPW file for the current building."""
        weather_provider = self._get_weather_provider()
        self.epw_file = weather_provider.get_epw_file(
            building=self.building,
            plz_codes_reader=read_plz_codes_data,
            stations_reader=get_weather_files_stations,
            coordinates_plz_reader=get_coordinates_plz,
            distance_calculator=calculate_minimum_distance_to_next_weather_station,
            filename_reader=get_filename_with_minimum_distance,
            coordinates_station_reader=get_coordinates_station,
            distance_reader=get_distance,
        )
        self._plz_codes_data = weather_provider.plz_codes_data

    def get_usage_time(self):
        """Return usage start and end for the current building."""
        return self._get_profile_provider().get_usage_time(
            building=self.building,
            profiles_zuweisungen_data=self.profiles_zuweisungen_data,
            usage_from_norm=self.usage_from_norm,
        )

    def get_gains(self):
        """Return person and appliance gains for the current building."""
        return self._get_profile_provider().get_gains(
            building=self.building,
            profiles_zuweisungen_data=self.profiles_zuweisungen_data,
            profile_from_norm=self.profile_from_norm,
            gains_from_group_values=self.gains_from_group_values,
        )