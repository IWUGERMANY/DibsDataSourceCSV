import pandas as pd
from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError


def _value(row: pd.DataFrame, column: str):
    """Return a scalar value from the single-row norm assignment DataFrame."""
    return row[column].iloc[0]


def _text_value(row: pd.DataFrame, column: str) -> str:
    """Return text values with the legacy pandas formatting used in summaries."""
    return row[column].to_string(index=False).strip()


def _raise_unsupported_gains_group(gains_from_group_values: str, norm: str) -> None:
    """Raise a DIBS input error for unsupported appliance-gain groups."""
    raise DIBSInputError(
        "Unsupported gains group value",
        phase="datasource.gains",
        context={
            "norm": norm,
            "gains_from_group_values": gains_from_group_values,
            "allowed_values": ["low", "mid", "max"],
        },
    )


def get_usage_start_end(usage_from_norm: str, row: pd.DataFrame) -> tuple[float, float]:
    """Return usage start and end hours for the selected norm source."""
    if usage_from_norm == "sia2024":
        return int(_value(row, "usage_start_sia2024")), int(
            _value(row, "usage_end_sia2024")
        )

    elif usage_from_norm == "mza":
        return float(_value(row, "usage_start_mza")), float(
            _value(row, "usage_end_mza")
        )

    return int(_value(row, "usage_start_18599")), int(
        _value(row, "usage_end_18599")
    )


def get_appliance_gains_sia2024(
    gains_from_group_values: str, row: pd.DataFrame
) -> float:
    """Return SIA2024 appliance gains for the selected low/mid/max group."""
    match gains_from_group_values:
        case "low":
            return float(_value(row, "appliance_gains_ziel_sia2024"))

        case "mid":
            return float(_value(row, "appliance_gains_standard_sia2024"))

        case "max":
            return float(_value(row, "appliance_gains_bestand_sia2024"))

    _raise_unsupported_gains_group(gains_from_group_values, "sia2024")


def get_appliance_gains_18599(gains_from_group_values: str, row: pd.DataFrame) -> float:
    """Return DIN18599 appliance gains for the selected low/mid/max group."""
    match gains_from_group_values:
        case "low":
            return float(_value(row, "appliance_gains_tief_18599"))

        case "mid":
            return float(_value(row, "appliance_gains_mittel_18599"))

        case "max":
            return float(_value(row, "appliance_gains_hoch_18599"))

    _raise_unsupported_gains_group(gains_from_group_values, "din18599")


def get_typ_norm_and_gain_per_person_sia2024(row: pd.DataFrame) -> tuple[float, str]:
    """Return SIA2024 person gain and type label from an assignment row."""
    return (
        float(_value(row, "gain_per_person_sia2024")),
        _text_value(row, "typ_sia2024"),
    )


def get_typ_norm_and_gain_per_person_18599(row: pd.DataFrame) -> tuple[float, str]:
    """Return DIN18599 person gain and type label from an assignment row."""
    return (
        float(_value(row, "gain_per_person_18599")),
        _text_value(row, "typ_18599"),
    )


def get_gain_per_person_and_appliance_and_typ_norm_sia2024(
    row: pd.DataFrame, gains_from_group_values: str
) -> tuple[tuple[float, str], float]:
    """Return SIA2024 person-gain tuple and appliance gains together."""
    return get_typ_norm_and_gain_per_person_sia2024(row), get_appliance_gains_sia2024(
        gains_from_group_values, row
    )


def get_gain_per_person_and_appliance_and_typ_norm_18599(
    row, gains_from_group_values: str
) -> tuple[tuple[float, str], float]:
    """Return DIN18599 person-gain tuple and appliance gains together."""
    return get_typ_norm_and_gain_per_person_18599(row), get_appliance_gains_18599(
        gains_from_group_values, row
    )


def get_typ_norm_and_gain_per_person_mza(row: pd.DataFrame) -> tuple[float, str]:
    """Return MZA person gain and type label from an assignment row."""
    return (
        float(_value(row, "gain_per_person_mza")),
        _text_value(row, "typ_mza"),
    )


def get_appliance_gains_mza(gains_from_group_values: str, row: pd.DataFrame) -> float:
    """Return MZA appliance gains for the selected low/mid/max group."""
    match gains_from_group_values:
        case "low":
            return float(_value(row, "appliance_gains_tief_mza"))

        case "mid":
            return float(_value(row, "appliance_gains_mittel_mza"))

        case "max":
            return float(_value(row, "appliance_gains_hoch_mza"))

    _raise_unsupported_gains_group(gains_from_group_values, "mza")


def get_gain_per_person_and_appliance_and_typ_norm_mza(
    row, gains_from_group_values: str
) -> tuple[tuple[float, str], float]:
    """Return MZA person-gain tuple and appliance gains together."""
    return get_typ_norm_and_gain_per_person_mza(row), get_appliance_gains_mza(
        gains_from_group_values, row
    )