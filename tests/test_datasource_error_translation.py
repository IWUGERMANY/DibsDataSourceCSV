import pandas as pd
import pytest
from pandas.errors import ParserError

from dibs_computing_core.iso_simulator.exceptions.base import DIBSDataSourceError
from dibs_computing_core.iso_simulator.exceptions.plz_exception import PLZNotFoundError
from dibs_datasource_csv.utils import utils_epwfile, utils_readcsv


def test_user_building_file_error_is_translated_without_absolute_path(monkeypatch):
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("C:/secret/path/input.csv")

    monkeypatch.setattr(utils_readcsv.pd, "read_csv", raise_file_not_found)

    with pytest.raises(DIBSDataSourceError) as caught:
        utils_readcsv.read_user_building("C:/secret/path/input.csv")

    assert caught.value.phase == "datasource.user_building"
    assert caught.value.context == {
        "file_type": "user_building_csv",
        "file_name": "input.csv",
        "error_type": "FileNotFoundError",
    }
    assert "secret" not in str(caught.value.context)


def test_weather_parser_error_is_translated(monkeypatch):
    def raise_parser_error(*args, **kwargs):
        raise ParserError("broken csv")

    monkeypatch.setattr(utils_readcsv.pd, "read_csv", raise_parser_error)

    with pytest.raises(DIBSDataSourceError) as caught:
        utils_readcsv.read_weather_data("C:/weather/weather.epw")

    assert caught.value.phase == "datasource.weather_data"
    assert caught.value.context == {
        "file_type": "weather_epw",
        "file_name": "weather.epw",
        "error_type": "ParserError",
    }


def test_unknown_plz_is_translated_to_plz_not_found_error():
    plz_data = pd.DataFrame(
        [{"zipcode": 12345, "latitude": 50.0, "longitude": 8.0}]
    )

    with pytest.raises(PLZNotFoundError) as caught:
        utils_epwfile.get_coordinates_plz(plz_data, 99999)

    assert caught.value.phase == "datasource.epw_file"
    assert caught.value.context == {"plz": 99999}


def test_weather_station_file_error_is_translated(monkeypatch):
    monkeypatch.setattr(utils_epwfile, "get_data_path", lambda: "C:/secret/data")

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("C:/secret/data/weatherfiles_stations_93.csv")

    monkeypatch.setattr(utils_epwfile.pd, "read_csv", raise_file_not_found)

    with pytest.raises(DIBSDataSourceError) as caught:
        utils_epwfile.get_weather_files_stations("2004-2018")

    assert caught.value.phase == "datasource.epw_file"
    assert caught.value.context == {
        "file_type": "weather_station_csv",
        "file_name": "weatherfiles_stations_93.csv",
        "weather_period": "2004-2018",
        "error_type": "FileNotFoundError",
    }
    assert "secret" not in str(caught.value.context)
