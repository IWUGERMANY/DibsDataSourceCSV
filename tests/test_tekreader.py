import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_datasource_csv.utils.utils_tekreader import (
    get_tek_data_frame_based_on_tek_name,
    get_tek_dhw,
)


def test_get_tek_data_frame_raises_for_unknown_category():
    values = pd.DataFrame(
        [{"TEK_Category": "Known", "TEK Warmwasser": "12.5"}]
    )

    with pytest.raises(DIBSInputError) as caught:
        get_tek_data_frame_based_on_tek_name(values, "Missing")

    assert caught.value.phase == "datasource.tek"
    assert caught.value.context == {"tek_name": "Missing"}


def test_get_tek_dhw_raises_for_empty_data_frame():
    with pytest.raises(DIBSInputError) as caught:
        get_tek_dhw(pd.DataFrame(columns=["TEK Warmwasser"]))

    assert caught.value.phase == "datasource.tek"
    assert caught.value.context == {"field": "TEK Warmwasser"}


def test_get_tek_dhw_returns_float_for_selected_category():
    values = pd.DataFrame(
        [{"TEK_Category": "Known", "TEK Warmwasser": "12.5"}]
    )

    selected = get_tek_data_frame_based_on_tek_name(values, "Known")

    assert get_tek_dhw(selected) == 12.5
