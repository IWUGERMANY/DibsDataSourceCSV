import pytest

import dibs_datasource_csv.datasource_csv as datasource_module
from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError


def patch_constructor_io(monkeypatch):
    monkeypatch.setattr(
        datasource_module,
        "read_occupancy_schedules_zuweisungen_data",
        lambda: "schedule_assignments",
    )
    monkeypatch.setattr(
        datasource_module,
        "read_vergleichswerte_zuweisung",
        lambda: "tek_assignment",
    )
    monkeypatch.setattr(
        datasource_module,
        "read_tek_nwg_comparative_values",
        lambda: "tek_values",
    )
    monkeypatch.setattr(
        datasource_module,
        "read_profiles_zuweisungen_data",
        lambda: "profile_assignment",
    )


def create_datasource(**overrides):
    args = {
        "data_path": "input.csv",
        "profile_from_norm": "din18599",
        "gains_from_group_values": "mid",
        "usage_from_norm": "sia2024",
        "weather_period": "2004-2018",
        "primary_energy_factor": "GEG",
    }
    args.update(overrides)
    return datasource_module.DataSourceCSV(**args)


def test_datasource_constructor_accepts_supported_options(monkeypatch):
    patch_constructor_io(monkeypatch)

    datasource = create_datasource()

    assert datasource.profile_from_norm == "din18599"
    assert datasource.gains_from_group_values == "mid"
    assert datasource.usage_from_norm == "sia2024"
    assert datasource.weather_period == "2004-2018"
    assert datasource.primary_energy_factor == "GEG"


@pytest.mark.parametrize(
    ("field", "value", "allowed_values"),
    [
        ("profile_from_norm", "wrong", ["din18599", "sia2024", "mza"]),
        ("gains_from_group_values", "medium", ["low", "mid", "max"]),
        ("usage_from_norm", "wrong", ["din18599", "sia2024", "mza"]),
        ("weather_period", "2020-2035", ["2004-2018", "2007-2021"]),
        ("primary_energy_factor", "DIN", ["GEG", "EPBD2020", "EPBD2030"]),
    ],
)
def test_datasource_constructor_rejects_unsupported_options(
    monkeypatch, field, value, allowed_values
):
    constructor_io_called = False

    def fail_if_called():
        nonlocal constructor_io_called
        constructor_io_called = True
        raise AssertionError("Constructor I/O should not run for invalid options")

    monkeypatch.setattr(
        datasource_module,
        "read_occupancy_schedules_zuweisungen_data",
        fail_if_called,
    )

    with pytest.raises(DIBSInputError) as caught:
        create_datasource(**{field: value})

    assert not constructor_io_called
    assert caught.value.phase == "datasource.init"
    assert caught.value.context == {
        "field": field,
        "value": value,
        "allowed_values": allowed_values,
    }
