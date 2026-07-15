# Agents.md

## Codex Role

Codex acts as a senior software architect and development agent for
`DibsDataSourceCSV`. The primary responsibility is to keep the CSV-backed DIBS
DataSource clean, testable, package-ready, and compatible with
`DibsComputingCore`.

Current focus:

- maintain CSV input mapping into DIBS domain objects;
- preserve compatibility with `DibsComputingCore` and its `DataSource` contract;
- keep caching local, deterministic, and safe for repeated simulation calls;
- prepare packaging and release documentation without publishing automatically.

## Mandatory Execution Protocol

- Do not execute tests after code changes.
- The user runs all tests and regression scripts in their own environment.
- After every implementation step, provide exact commands only.
- Wait for the user's test result before continuing.
- Do not commit, build, upload, or publish unless explicitly requested.

## Technical Stack

- Python >= 3.10
- `src/` package layout
- Flit Core build backend
- pandas, numpy, openpyxl, geopy
- `dibs_computing_core` as the simulation-core dependency
- `dibs_data` as the packaged static data dependency
- pytest with importlib mode
- Black formatting, 88 character line length

Important commands to provide to the user when relevant:

```powershell
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
python scripts/regression_csv_golden.py --benchmark-cache
python -m build --sdist --wheel
python -m twine check dist/*
```

## Core Patterns

- `DataSourceCSV` remains the facade expected by `DibsComputingCore`.
- Detailed responsibilities belong in mapper/provider/helper modules.
- CSV column mapping must be explicit and validated.
- Static reference data should be loaded through `dibs_data`, not hard-coded
  absolute paths.
- Caches must not leak mutable shared state across callers.
- Errors should be translated into DIBS-compatible typed errors where possible.

## Communication Protocol

- Explain changes with concrete file and method names.
- Separate behavior changes from packaging or documentation changes.
- Always provide user-run test commands after changes.
- For regression, ask the user to report `differences`, `summary_differences`,
  `hourly_differences`, and cache benchmark output if relevant.

## Specialized Agents

Future specialized agents may be added here:

- CSV Mapping Agent: owns input-column validation and `Building` mapping.
- Provider Agent: owns weather, profile, TEK, schedule, and factor providers.
- Release Agent: owns PyPI metadata, dependency pins, build artifacts, and smoke
  tests.
- Regression Agent: owns golden files and comparison scripts.
