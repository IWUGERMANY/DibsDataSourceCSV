# Packaging Checklist

Use this checklist before publishing `dibs_datasource_csv` to PyPI.

## 1. Dependency State

- Confirm `dibs_computing_core` is available in the desired version.
- Confirm `dibs_data` is available in the desired version.
- Replace development branch dependencies in `pyproject.toml` with released
  versions if this package should be installable directly from PyPI.
- Keep Git dependencies only for internal/dev builds.

## 2. Versioning

- Update `[project].version` in `pyproject.toml`.
- Use a new version for every uploaded PyPI artifact. PyPI does not allow
  overwriting an existing version.

## 3. Validation

Run:

```powershell
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
python scripts/regression_csv_golden.py --benchmark-cache
```

Expected regression result:

```text
differences=0
summary_differences=0
hourly_differences=0
```

## 4. Build

Run:

```powershell
python -m build
python -m twine check dist/*
```

If `build` or `twine` is missing:

```powershell
python -m pip install build twine
```

## 5. Upload

TestPyPI first when dependency metadata changed:

```powershell
python -m twine upload --repository testpypi dist/*
```

PyPI release:

```powershell
python -m twine upload dist/*
```

## 6. Smoke Test In A Fresh Environment

Create a new virtual environment and verify:

```powershell
python -m venv .venv-smoke
.\.venv-smoke\Scripts\Activate.ps1
python -m pip install dibs_datasource_csv
python -c "from dibs_datasource_csv import DataSourceCSV; print(DataSourceCSV)"
```

If this import fails, check dependency metadata and package exports before
publishing the next version.
