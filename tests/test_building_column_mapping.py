import pandas as pd
import pytest

import dibs_datasource_csv.datasource_csv as datasource_module
from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError


class FakeBuilding:
    def __init__(self, *values):
        self.values = values


def make_datasource():
    datasource = datasource_module.DataSourceCSV.__new__(
        datasource_module.DataSourceCSV
    )
    datasource.data_path = "input.csv"
    return datasource


def one_building_dataframe(columns=None):
    if columns is None:
        columns = list(datasource_module.EXPECTED_BUILDING_COLUMNS)
    return pd.DataFrame([{column: column for column in columns}], columns=columns)


def test_get_user_buildings_maps_by_expected_column_order(monkeypatch):
    reversed_columns = list(reversed(datasource_module.EXPECTED_BUILDING_COLUMNS))
    monkeypatch.setattr(
        datasource_module,
        "read_user_buildings",
        lambda path: one_building_dataframe(reversed_columns),
    )
    monkeypatch.setattr(datasource_module, "Building", FakeBuilding)

    datasource = make_datasource()
    datasource.get_user_buildings()

    assert len(datasource.buildings) == 1
    assert datasource.buildings[0].values == datasource_module.EXPECTED_BUILDING_COLUMNS


def test_get_user_building_rejects_missing_extra_and_duplicate_columns(monkeypatch):
    expected = list(datasource_module.EXPECTED_BUILDING_COLUMNS)
    broken_columns = expected[1:] + ["unexpected_column", expected[1]]
    broken_data = pd.DataFrame([list(range(len(broken_columns)))], columns=broken_columns)
    monkeypatch.setattr(datasource_module, "read_user_building", lambda path: broken_data)

    datasource = make_datasource()

    with pytest.raises(DIBSInputError) as caught:
        datasource.get_user_building()

    assert caught.value.phase == "datasource.user_building"
    assert caught.value.context["missing_columns"] == [expected[0]]
    assert caught.value.context["extra_columns"] == ["unexpected_column"]
    assert caught.value.context["duplicate_columns"] == [expected[1]]