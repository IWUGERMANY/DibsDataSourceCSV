"""Primary energy and emission factor mapping for DataSourceCSV."""

import pandas as pd

from dibs_computing_core.iso_simulator.exceptions.base import DIBSInputError
from dibs_computing_core.iso_simulator.model.primary_energy_and_emission_factors import (
    PrimaryEnergyAndEmissionFactor,
)

from ..utils.utils_readcsv import read_gwp_pe_factors_data


PRIMARY_ENERGY_FACTOR_COLUMNS = {
    "GEG": "Primary Energy Factor GEG   [-]",
    "EPBD2020": "Primary Energy Factor,tot EPBD2020   [-]",
    "EPBD2030": "Primary Energy Factor,tot EPBD2030   [-]",
}


def get_primary_energy_factor_column(primary_energy_factor: str) -> str:
    """Return the CSV column used for the selected primary energy factor standard."""
    column_name = PRIMARY_ENERGY_FACTOR_COLUMNS.get(primary_energy_factor)
    if column_name is None:
        raise DIBSInputError(
            "Unknown primary energy factor",
            phase="datasource.primary_energy_factors",
            context={"primary_energy_factor": primary_energy_factor},
        )
    return column_name


def build_primary_energy_and_emission_factors(
    gwp_pe_factors: pd.DataFrame, primary_energy_factor: str
) -> list[PrimaryEnergyAndEmissionFactor]:
    """Build DIBS factor objects from the raw GWP/PE factor table."""
    column_name = get_primary_energy_factor_column(primary_energy_factor)
    epw_pe_factors = []
    for _, row in gwp_pe_factors.iterrows():
        epw_pe_factors.append(
            PrimaryEnergyAndEmissionFactor(
                energy_carrier=row["Energy Carrier"],
                primary_energy_factor_GEG=row[column_name],
                relation_calorific_to_heating_value_GEG=row[
                    "Relation Calorific to Heating Value GEG  [-]"
                ],
                gwp_spezific_to_heating_value_GEG=row[
                    "GWP spezific to heating value GEG [g/kWh]"
                ],
                use=row["Use"],
            )
        )
    return epw_pe_factors


def get_epw_pe_factors(primary_energy_factor: str) -> list[PrimaryEnergyAndEmissionFactor]:
    """Read and map primary energy and emission factors for DataSourceCSV."""
    return build_primary_energy_and_emission_factors(
        read_gwp_pe_factors_data(), primary_energy_factor
    )
