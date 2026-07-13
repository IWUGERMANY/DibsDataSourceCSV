import pandas as pd

from dibs_datasource_csv.utils import utils_readcsv


def test_public_csv_readers_are_annotated_as_dataframes():
    reader_names = [
        "read_user_building",
        "read_user_buildings",
        "read_gwp_pe_factors_data",
        "read_plz_codes_data",
        "read_profiles_zuweisungen_data",
        "read_occupancy_schedules_zuweisungen_data",
        "read_schedule_file",
        "read_weather_data",
        "read_vergleichswerte_zuweisung",
        "read_tek_nwg_comparative_values",
    ]

    for reader_name in reader_names:
        reader = getattr(utils_readcsv, reader_name)
        assert reader.__annotations__["return"] is pd.DataFrame
