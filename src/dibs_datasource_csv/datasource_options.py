"""Constructor option validation for DataSourceCSV."""

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError


ALLOWED_DATASOURCE_OPTIONS = {
    "profile_from_norm": ("din18599", "sia2024", "mza"),
    "gains_from_group_values": ("low", "mid", "max"),
    "usage_from_norm": ("din18599", "sia2024", "mza"),
    "weather_period": ("2004-2018", "2007-2021"),
    "primary_energy_factor": ("GEG", "EPBD2020", "EPBD2030"),
}


def validate_datasource_options(**options) -> None:
    """Validate constructor options before any reference CSV data is loaded."""
    for field, value in options.items():
        allowed_values = ALLOWED_DATASOURCE_OPTIONS[field]
        if value not in allowed_values:
            raise DIBSInputError(
                "Unsupported DataSourceCSV option",
                phase="datasource.init",
                context={
                    "field": field,
                    "value": value,
                    "allowed_values": list(allowed_values),
                },
            )
