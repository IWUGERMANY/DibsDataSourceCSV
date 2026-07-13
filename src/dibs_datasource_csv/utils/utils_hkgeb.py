"""
Helpers for resolving building usage type pairs.

`hk_geb` is the main usage category and `uk_geb` is the subcategory. Both
values must be resolved together because the same `uk_geb` can only be valid in
context of the matching `hk_geb` row.
"""

from pandas import DataFrame


def find_hk_uk_rows(zuweisungen: DataFrame, hk_geb: str, uk_geb: str) -> DataFrame:
    """Return rows matching the exact `(hk_geb, uk_geb)` pair."""
    return zuweisungen[
        (zuweisungen["hk_geb"] == hk_geb) & (zuweisungen["uk_geb"] == uk_geb)
    ]
