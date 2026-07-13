import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_datasource_csv.providers.factor_provider import (
    build_primary_energy_and_emission_factors,
    get_primary_energy_factor_column,
)


def _factor_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Energy Carrier": "Electricity grid mix",
                "Primary Energy Factor GEG   [-]": 1.8,
                "Primary Energy Factor,tot EPBD2020   [-]": 1.5,
                "Primary Energy Factor,tot EPBD2030   [-]": 1.2,
                "Relation Calorific to Heating Value GEG  [-]": 1.0,
                "GWP spezific to heating value GEG [g/kWh]": 560,
                "Use": "lighting",
            }
        ]
    )


def test_unknown_primary_energy_factor_raises_dibs_input_error():
    with pytest.raises(DIBSInputError) as caught:
        get_primary_energy_factor_column("unknown")

    assert caught.value.phase == "datasource.primary_energy_factors"
    assert caught.value.context == {"primary_energy_factor": "unknown"}


def test_build_primary_energy_and_emission_factors_uses_selected_column():
    factors = build_primary_energy_and_emission_factors(_factor_table(), "EPBD2030")

    assert len(factors) == 1
    assert factors[0].energy_carrier == "Electricity grid mix"
    assert factors[0].primary_energy_factor_GEG == 1.2
    assert factors[0].relation_calorific_to_heating_value_GEG == 1.0
    assert factors[0].gwp_spezific_to_heating_value_GEG == 560
    assert factors[0].use == "lighting"
