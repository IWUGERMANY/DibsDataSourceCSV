# DibsDataSourceCSV

`DibsDataSourceCSV` is the CSV-backed `DataSource` implementation for
`DibsComputingCore`. It reads DIBS input data from CSV/reference files, maps the
rows to DIBS domain objects, and provides the data through the `DataSource`
interface used by the DIBS simulation core.

The package does not implement the simulation itself. The simulation is executed
by `dibs_computing_core`; this package is responsible for CSV input, lookup
files, weather/EPW resolution, schedules, TEK values, gains, usage times, and
primary-energy/emission factors.

## Architecture

```text
src/dibs_datasource_csv/
  datasource_csv.py              # Thin DataSource facade used by DibsComputingCore
  datasource_options.py          # Constructor option validation
  building_mapper.py             # Building CSV column validation and Building mapping
  providers/
    factor_provider.py           # PrimaryEnergyAndEmissionFactor mapping
    profile_provider.py          # HK/UK lookup, schedules, usage time, gains
    tek_provider.py              # TEK category and DHW lookup
    weather_provider.py          # EPW selection, WeatherData loading, weather caches
  utils/
    utils_readcsv.py             # CSV readers and DataSource error translation
    utils_epwfile.py             # PLZ/station/weather helper functions
    utils_normreader.py          # Norm profile value extraction
    utils_hkgeb.py               # HK/UK pair matching
    utils_schedule.py            # Schedule-name extraction
    utils_tekreader.py           # TEK helper functions
```

`DataSourceCSV` intentionally remains a facade because `DibsComputingCore`
expects a stateful `DataSource` object. The detailed responsibilities are split
into mapper/provider modules so they can be tested independently.

## Installation

```powershell
pip install dibs_datasource_csv
```

For local development:

```powershell
pip install -e .
```

## Usage

```python
from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
from dibs_datasource_csv import DataSourceCSV

source = DataSourceCSV(
    data_path="path/to/SimulationData_Breitenerhebung.csv",
    profile_from_norm="din18599",
    gains_from_group_values="mid",
    usage_from_norm="sia2024",
    weather_period="2004-2018",
    primary_energy_factor="GEG",
)

dibs = DIBS(source)
simulation_time, hourly_results, summary_results = dibs.multi()
```

For a single building, use the corresponding `DIBS` method from
`dibs_computing_core`, for example `calculate_result_of_one_building()`.

## Constructor Options

| Option | Meaning | Common values |
|---|---|---|
| `data_path` | CSV file with building input rows | `SimulationData_Breitenerhebung.csv` |
| `profile_from_norm` | Norm source for profile gains | `din18599`, `sia2024`, `mza` |
| `gains_from_group_values` | Norm gain group | `low`, `mid`, `max` |
| `usage_from_norm` | Norm source for usage time | `din18599`, `sia2024`, `mza` |
| `weather_period` | EPW weather-data period | `2004-2018`, `2007-2021` |
| `primary_energy_factor` | Primary-energy/emission factor source | `GEG` |

Invalid options are rejected at construction time with DIBS-typed input errors.

## Caching Behavior

Caches are per `DataSourceCSV` instance, not global process caches.

- Weather data is cached by `(weather_period, epw_file.file_name)`.
- EPW file selection is cached by `(weather_period, plz)`.
- Weather-station tables are cached by `weather_period`.
- Schedule files are cached by `schedule_name`.

The caches avoid repeated file parsing inside one simulation run while keeping
results stable. Returned lists are recreated from cached tuples where sharing a
mutable list would be risky.

## Testing

Run the unit tests:

```powershell
python -m pytest -q -p no:cacheprovider tests
```

Run the golden regression for the nine-building CSV scenario:

```powershell
python scripts/regression_csv_golden.py
```

Optional cache benchmark:

```powershell
python scripts/regression_csv_golden.py --benchmark-cache
```

The golden regression should report:

```text
differences=0
summary_differences=0
hourly_differences=0
```

## Release Notes For Maintainers

Before publishing a new PyPI version, check `PACKAGING_CHECKLIST.md`. In
particular, make sure dependencies on `dibs_computing_core` and `dibs_data` point
to published package versions instead of development branches, if the release is
intended for public installation from PyPI.

## License

This repository is licensed under the [MIT License](LICENSE).
