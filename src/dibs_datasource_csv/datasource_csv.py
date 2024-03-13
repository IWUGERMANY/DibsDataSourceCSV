"""
This class is one of the implementations of the interface DataSource. This class handles with data from csv files processed with pandas python module
"""

import os
import pandas as pd

from dibs_computing_core.iso_simulator.data_source.datasource import DataSource

from .utils.utils_epwfile import (
    get_coordinates_plz,
    get_weather_files_stations,
    calculate_minimum_distance_to_next_weather_station,
    get_filename_with_minimum_distance,
    get_coordinates_station,
    get_distance,
)
from .utils.utils_normreader import (
    find_row,
    get_usage_start_end,
    get_gain_per_person_and_appliance_and_typ_norm_sia2024,
    get_gain_per_person_and_appliance_and_typ_norm_18599,
)
from .utils.utils_readcsv import (
    read_gwp_pe_factors_data,
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
from .utils.utils_hkgeb import (
    hk_and_uk_in_zuweisungen,
    hk_or_uk_not_in_zuweisungen,
    hk_in_zuweisungen,
    uk_in_zuweisungen,
)
from .utils.utils_tekreader import (
    get_tek_name,
    get_tek_data_frame_based_on_tek_name,
    get_tek_dhw,
)
from .utils.utils_schedule import get_schedule_name

from dibs_computing_core.iso_simulator.model.schedule_name import ScheduleName
from dibs_computing_core.iso_simulator.model.building import Building
from dibs_computing_core.iso_simulator.model.primary_energy_and_emission_factors import (
    PrimaryEnergyAndEmissionFactor,
)
from dibs_computing_core.iso_simulator.model.weather_data import WeatherData
from dibs_computing_core.iso_simulator.model.epw_file import EPWFile
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)
from dibs_computing_core.iso_simulator.exceptions.usage_time_exception import (
    UsageTimeError,
)

from dibs_daten.data_utils import get_data_path


class DataSourceCSV(DataSource):
    def __init__(
        self,
        data_path: str,
        profile_from_norm: str,
        gains_from_group_values: str,
        usage_from_norm: str,
        weather_period: str,
    ):
        self.data_path = data_path
        self.profile_from_norm = profile_from_norm
        self.gains_from_group_values = gains_from_group_values
        self.usage_from_norm = usage_from_norm
        self.weather_period = weather_period
        # self.path_to_epw_file = os.path.join('iso_simulator', 'auxiliary', 'weather_data')
        self.epw_file = None
        self.epw_pe_factors = None
        self.building = None
        self.buildings = None

    """
    This constructor to initialize an instance of the DataSourceCSV class
    """

    def get_user_building(self):
        """
        This method reads the file which contains the building data to simulate.
        Args:

        Returns:
            building
        Return type:
            Building
        """
        building_data: pd.DataFrame | None = read_user_building(self.data_path)
        self.building = Building(*building_data.iloc[0].values)

    def get_user_buildings(self):
        """
        This method reads the file which contains the building data to simulate.
        Args:

        Returns:
            buildings
        Return type:
            list [Building]
        """
        building_data: pd.DataFrame = read_user_buildings(self.data_path)
        self.buildings = [Building(*row.values) for _, row in building_data.iterrows()]

    def get_epw_pe_factors(self):
        """
        This method retrieves all primary energy and emission factors from this file
        'Primary_energy_and_emission_factors.csv' which is in the module dibs_data
        Returns:
            epw_pe_factors
        Return type:
            list[PrimaryEnergyAndEmissionFactor]
        """
        gwp_pe_factors: pd.DataFrame = read_gwp_pe_factors_data()

        self.epw_pe_factors = [
            PrimaryEnergyAndEmissionFactor(*row.values)
            for _, row in gwp_pe_factors.iterrows()
        ]

    def get_schedule(self):
        """
        Find occupancy schedule from SIA2024, depending on hk_geb, uk_geb from csv file
        'occupancy_schedules_zuweisungen.csv' which is in the module dibs_data
        Args:

        Returns:
            (schedule_name_list, schedule_name) or throws an error
        Return type:
            Union[Tuple[List[ScheduleName], str], HkOrUkNotFoundError]
        """
        data: pd.DataFrame = read_occupancy_schedules_zuweisungen_data()

        try:
            if not hk_and_uk_in_zuweisungen(
                data, self.building.hk_geb, self.building.uk_geb
            ):
                raise HkOrUkNotFoundError("hk or uk unknown")
            row: pd.DataFrame = find_row(data, self.building.uk_geb)
            schedule_name: str = get_schedule_name(row)
            schedule_file: pd.DataFrame = read_schedule_file(schedule_name)

            return (
                [ScheduleName(*row.values) for _, row in schedule_file.iterrows()],
                schedule_name,
                schedule_file.People.sum(),
            )
        except HkOrUkNotFoundError as error:
            print(error)

    def get_tek(self):
        """
        Find TEK values from Partial energy parameters to build the comparative values in accordance with the
        announcement  of 15.04.2021 on the Building Energy Act (GEG) of 2020, depending on hk_geb, uk_geb
        File names used:
            - 'TEK_NWG_Vergleichswerte_zuweisung.csv' and TEK_NWG_Vergleichswerte.csv which are in the module dibs_data
        Args:

        Returns:
            tek_dhw, tek_name or throws an error
        Return type:
            Union[Tuple[float, str], ValueError]
        """
        data: pd.DataFrame = read_vergleichswerte_zuweisung()
        db_teks: pd.DataFrame = read_tek_nwg_comparative_values()

        try:
            if hk_or_uk_not_in_zuweisungen(
                data, self.building.hk_geb, self.building.uk_geb
            ):
                raise HkOrUkNotFoundError("hk or uk unknown")
            row: pd.DataFrame = find_row(data, self.building.uk_geb)
            tek_name: str = get_tek_name(row)
            df_tek: pd.DataFrame = get_tek_data_frame_based_on_tek_name(
                db_teks, tek_name
            )
            tek_dhw: float = get_tek_dhw(df_tek)
            return tek_dhw, tek_name
        except HkOrUkNotFoundError as error:
            print(error)

    def choose_and_get_the_right_weather_data_from_path(self):
        """
        This method retrieves the right weather data according to the given weather_period and file_name
        Args:

        Returns:
            weather_data_objects
        Return type:
            List[WeatherData]
        """
        path_data = get_data_path()

        if self.weather_period == "2007-2021":
            weather_data: pd.DataFrame = read_weather_data(
                os.path.join(
                    path_data,
                    "auxiliary",
                    "weather_data_TMYx_2007_2021",
                    self.epw_file.file_name,
                )
            )
        else:
            weather_data: pd.DataFrame = read_weather_data(
                os.path.join(
                    path_data, "auxiliary", "weather_data", self.epw_file.file_name
                )
            )

        return [WeatherData(*row.values) for _, row in weather_data.iterrows()]

    def get_epw_file(self) -> EPWFile:
        """
        This method finds the epw file depending on building location, Pick latitude and longitude from plz_data and put
        values into a list and Calculate minimum distance to next weather station

        Args:

         File names used:
            - 'weather_data/plzcodes.csv', 'weatherfiles_stations_109.csv' and 'weatherfiles_stations_93.csv' which are in the module dibs_data

        Returns:
            epw_file object
        Return type:
            EPWFile
        """
        plz_data: pd.DataFrame = read_plz_codes_data()

        weather_files_stations: pd.DataFrame = get_weather_files_stations(
            self.weather_period
        )

        (
            weather_files_stations["latitude_building"],
            weather_files_stations["longitude_building"],
        ) = get_coordinates_plz(plz_data, self.building.plz)

        calculate_minimum_distance_to_next_weather_station(weather_files_stations)

        epw_filename: str = get_filename_with_minimum_distance(weather_files_stations)

        coordinates_station: list = get_coordinates_station(weather_files_stations)

        distance: float = get_distance(weather_files_stations)

        self.epw_file = EPWFile(epw_filename, coordinates_station, distance)

    def get_usage_time(self):
        """
        Find building's usage time DIN 18599-10 or SIA2024
        Args:

        File name used:
            - 'profiles_zuweisungen.csv' which is in the module dibs_data

        Returns:
            usage_start, usage_end or throws error
        Return type:
            Union[Tuple[int, int], ValueError]
        """

        gains_zuweisungen: pd.DataFrame = read_profiles_zuweisungen_data()

        try:
            if hk_in_zuweisungen(self.building.hk_geb, gains_zuweisungen):
                if not uk_in_zuweisungen(self.building.uk_geb, gains_zuweisungen):
                    raise UsageTimeError(
                        "Something went wrong with the function getUsagetime()"
                    )
                row: pd.DataFrame = find_row(gains_zuweisungen, self.building.uk_geb)
                return get_usage_start_end(str(self.usage_from_norm), row)
        except UsageTimeError as error:
            print(error)

    def get_gains(self):
        """
        Find data from DIN V 18599-10 or SIA2024
        Args:
            hk_geb: Usage type (main category)
            uk_geb: Usage type (subcategory)
            profile_from_norm: data source either 18599-10 or SIA2024 [muss be provided by the user]
            gains_from_group_values: group in norm low/medium/high [muss be provided by th]
        File name used:
            - 'profiles_zuweisungen.csv' which is in the module dibs_data

        Returns:
            gain_person_and_typ_norm, appliance_gains
        Return type:
            Tuple[Tuple[float, str], float]
        """

        data: pd.DataFrame = read_profiles_zuweisungen_data()

        if hk_and_uk_in_zuweisungen(data, self.building.hk_geb, self.building.uk_geb):
            row: pd.DataFrame = find_row(data, self.building.uk_geb)

            gain_person_and_typ_norm: tuple[float, str]
            appliance_gains: float

            if self.profile_from_norm == "sia2024":
                (
                    gain_person_and_typ_norm,
                    appliance_gains,
                ) = get_gain_per_person_and_appliance_and_typ_norm_sia2024(
                    self.gains_from_group_values, row
                )

            else:
                (
                    gain_person_and_typ_norm,
                    appliance_gains,
                ) = get_gain_per_person_and_appliance_and_typ_norm_18599(
                    row, self.gains_from_group_values
                )

        return gain_person_and_typ_norm, appliance_gains
