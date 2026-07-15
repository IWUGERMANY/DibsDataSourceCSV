# PROJECT_CONTEXT.md

## Project Goal

`DibsDataSourceCSV` is the CSV-backed `DataSource` implementation for
`DibsComputingCore`. It reads building input rows and reference data, maps them
to DIBS domain objects, and supplies the simulation core with buildings, weather,
profiles, schedules, TEK values, usage times, gains, and energy/emission factors.

The package does not run the simulation formulas itself. Simulation is performed
by `DibsComputingCore`.

## Architecture Decisions

- `DataSourceCSV` remains a thin facade because the computing core expects a
  stateful `DataSource` object.
- Detailed logic is split into `building_mapper.py`, provider modules, and utils.
- Static data access goes through `dibs_data` so the package can work after PyPI
  installation.
- Golden regression protects the nine-building CSV scenario.
- Caches are instance-local and must keep outputs stable.

## Directory Structure

```text
src/dibs_datasource_csv/
  datasource_csv.py        # public DataSource facade
  datasource_options.py    # constructor option validation
  building_mapper.py       # CSV column validation and Building mapping
  providers/
    factor_provider.py     # primary energy and emission factors
    profile_provider.py    # HK/UK lookup, schedules, gains, usage times
    tek_provider.py        # TEK and DHW lookup
    weather_provider.py    # EPW/weather selection and weather caches
  utils/
    utils_readcsv.py       # CSV readers and error translation
    utils_epwfile.py       # EPW/weather helper functions
    utils_hkgeb.py         # HK/UK matching
    utils_normreader.py    # norm profile values
    utils_schedule.py      # schedule name extraction
    utils_tekreader.py     # TEK helpers
scripts/
  regression_csv_golden.py # golden regression and cache benchmark
tests/                     # unit and contract tests
```

## Data Flow

```text
SimulationData_Breitenerhebung.csv
  -> DataSourceCSV constructor options
  -> CSV readers and building mapper
  -> providers for weather/profile/TEK/factors
  -> DIBS DataSource interface
  -> DibsComputingCore DIBS.multi() or one-building simulation
```

## Current Project State

Implemented and documented:

- error handling integration;
- CSV column validation;
- provider split and facade cleanup;
- HK/UK matching improvements;
- local caches for weather, EPW selection, schedules, and reference data;
- golden regression and cache benchmark scripts;
- packaging checklist for later PyPI release.

## Next Milestones

- Replace development Git dependencies with released package versions before a
  public PyPI upload.
- Run user-led tests and golden regression before release.
- Build wheel/sdist only after dependency versions are finalized.
- Smoke-test the built wheel in a fresh environment.

## Known Constraints

- The user executes all tests manually.
- Public PyPI release should not depend on branch snapshots unless explicitly
  intended as an internal/dev release.
- Regression must keep `differences=0`, `summary_differences=0`, and
  `hourly_differences=0` for refactors without intended behavior changes.
- Build artifacts in `dist/` should be recreated for each release and not reused
  from old versions.
