from types import SimpleNamespace

import pandas as pd
import pytest

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.exceptions.uk_or_hk_exception import (
    HkOrUkNotFoundError,
)
from dibs_datasource_csv.providers.tek_provider import get_tek


def _building():
    return SimpleNamespace(hk_geb="HK", uk_geb="UK")


def test_tek_provider_rejects_missing_hk_uk_pair():
    assignment = pd.DataFrame([{"hk_geb": "HK", "uk_geb": "OTHER", "TEK": "Known"}])

    with pytest.raises(HkOrUkNotFoundError) as caught:
        get_tek(
            vergleichswerte_zuweisung=assignment,
            tek_nwg_comparative_values=pd.DataFrame(),
            building=_building(),
        )

    assert caught.value.phase == "datasource.tek"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK"}


def test_tek_provider_rejects_duplicate_hk_uk_pair():
    assignment = pd.DataFrame(
        [
            {"hk_geb": "HK", "uk_geb": "UK", "TEK": "Known"},
            {"hk_geb": "HK", "uk_geb": "UK", "TEK": "Known"},
        ]
    )

    with pytest.raises(DIBSInputError) as caught:
        get_tek(
            vergleichswerte_zuweisung=assignment,
            tek_nwg_comparative_values=pd.DataFrame(),
            building=_building(),
        )

    assert caught.value.phase == "datasource.tek"
    assert caught.value.context == {"hk_geb": "HK", "uk_geb": "UK", "matches": 2}


def test_tek_provider_returns_dhw_and_name():
    assignment = pd.DataFrame([{"hk_geb": "HK", "uk_geb": "UK", "TEK": "Known"}])
    tek_values = pd.DataFrame([{"TEK_Category": "Known", "TEK Warmwasser": "12.5"}])

    assert get_tek(
        vergleichswerte_zuweisung=assignment,
        tek_nwg_comparative_values=tek_values,
        building=_building(),
    ) == (12.5, "Known")
