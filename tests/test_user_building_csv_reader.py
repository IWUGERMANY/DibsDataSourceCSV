import pandas as pd
import pytest

from dibs_datasource_csv.utils import utils_readcsv


def test_read_user_building_reads_only_first_row(monkeypatch):
    calls = []

    def fake_safe_read_csv(data_path, **kwargs):
        calls.append((data_path, kwargs))
        return pd.DataFrame(
            [
                {"numeric": "1", "text": "NoHeating"},
            ]
        )

    monkeypatch.setattr(utils_readcsv, "_safe_read_csv", fake_safe_read_csv)

    dataframe = utils_readcsv.read_user_building("input.csv")

    assert calls[0][0] == "input.csv"
    assert calls[0][1]["phase"] == "datasource.user_building"
    assert calls[0][1]["file_type"] == "user_building_csv"
    assert calls[0][1]["nrows"] == 1
    assert dataframe.loc[0, "numeric"] == 1
    assert dataframe.loc[0, "text"] == "NoHeating"


def test_read_user_buildings_reads_all_rows(monkeypatch):
    calls = []

    def fake_safe_read_csv(data_path, **kwargs):
        calls.append((data_path, kwargs))
        return pd.DataFrame(
            [
                {"numeric": "1", "text": "NoHeating"},
                {"numeric": "2", "text": "GasBoilerCondensingFrom95"},
            ]
        )

    monkeypatch.setattr(utils_readcsv, "_safe_read_csv", fake_safe_read_csv)

    dataframe = utils_readcsv.read_user_buildings("input.csv")

    assert calls[0][1]["phase"] == "datasource.user_buildings"
    assert calls[0][1]["file_type"] == "user_buildings_csv"
    assert calls[0][1]["nrows"] is None
    assert list(dataframe["numeric"]) == [1, 2]
    assert list(dataframe["text"]) == ["NoHeating", "GasBoilerCondensingFrom95"]


def test_numeric_conversion_does_not_swallow_unexpected_errors(monkeypatch):
    dataframe = pd.DataFrame([{"numeric": "1"}])

    def raise_unexpected_error(values):
        raise RuntimeError("unexpected conversion failure")

    monkeypatch.setattr(utils_readcsv.pd, "to_numeric", raise_unexpected_error)

    with pytest.raises(RuntimeError):
        utils_readcsv._convert_numeric_columns(dataframe)
