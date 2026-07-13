import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_datasource_csv.utils.utils_normreader import (
    get_appliance_gains_18599,
    get_appliance_gains_mza,
    get_appliance_gains_sia2024,
)


def _norm_row() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "appliance_gains_ziel_sia2024": 1.0,
                "appliance_gains_standard_sia2024": 2.0,
                "appliance_gains_bestand_sia2024": 3.0,
                "appliance_gains_tief_18599": 4.0,
                "appliance_gains_mittel_18599": 5.0,
                "appliance_gains_hoch_18599": 6.0,
                "appliance_gains_tief_mza": 7.0,
                "appliance_gains_mittel_mza": 8.0,
                "appliance_gains_hoch_mza": 9.0,
            }
        ]
    )


@pytest.mark.parametrize(
    ("function", "norm"),
    [
        (get_appliance_gains_sia2024, "sia2024"),
        (get_appliance_gains_18599, "din18599"),
        (get_appliance_gains_mza, "mza"),
    ],
)
def test_invalid_gains_group_raises_dibs_input_error(function, norm):
    with pytest.raises(DIBSInputError) as caught:
        function("medium", _norm_row())

    assert caught.value.phase == "datasource.gains"
    assert caught.value.context == {
        "norm": norm,
        "gains_from_group_values": "medium",
        "allowed_values": ["low", "mid", "max"],
    }
