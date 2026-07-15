# Packaging Checklist

Use this checklist before publishing `dibs_datasource_csv` to PyPI.

## Current Release State

The package is prepared for a later release, but the final PyPI upload should
only happen after dependency versions are finalized.

Current blockers before public PyPI upload:

- `pyproject.toml` currently uses development Git dependencies for
  `dibs_computing_core` and `dibs_data`.
- For a clean public release, replace those Git dependencies with released PyPI
  versions, for example `dibs_computing_core == x.y.z` and `dibs_data == x.y.z`.
- Do not upload while `dist/` still contains old artifacts from another version.

## 1. Dependency State

Check `[project].dependencies` in `pyproject.toml`.

Acceptable for internal/dev builds:

```toml
dibs_computing_core @ git+https://...
dibs_data @ git+https://...
```

Recommended for public PyPI releases:

```toml
dibs_computing_core == <released-version>
dibs_data == <released-version>
```

Reason: users installing from PyPI should get reproducible dependencies from
published package versions instead of branch snapshots.

## 2. Versioning

- Update `[project].version` in `pyproject.toml`.
- Use a new version for every uploaded PyPI artifact. PyPI does not allow
  overwriting an existing version.
- Recommended next version after `1.0.2` is `1.0.3`, unless the dependency/API
  changes require a larger version bump.

## 3. Validation

Run from the repository root:

```powershell
cd "C:\Users\wail\Desktop\Projects\Stand dibs\DibsDataSourceCSV"
python -m pytest -q -p no:cacheprovider tests
python scripts\regression_csv_golden.py
python scripts\regression_csv_golden.py --benchmark-cache
```

Expected regression result:

```text
differences=0
summary_differences=0
hourly_differences=0
```

The cache benchmark does not need a fixed speedup number, but it must keep:

```text
differences=0
summary_differences=0
hourly_differences=0
```

## 4. Clean Old Build Artifacts

Before building, remove old artifacts:

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

This prevents accidentally uploading old files such as `1.0.1` while preparing a
new release.

## 5. Build

Install build tooling if needed:

```powershell
python -m pip install -e .[dev]
```

Build source distribution and wheel:

```powershell
python -m build --sdist --wheel
python -m twine check dist\*
```

Expected `twine check` result:

```text
PASSED
```

## 6. Smoke Test In A Fresh Environment

Create a new virtual environment and verify the built wheel before upload:

```powershell
python -m venv .venv-smoke
.\.venv-smoke\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install dist\dibs_datasource_csv-<version>-py3-none-any.whl
python -c "from dibs_datasource_csv import DataSourceCSV; print(DataSourceCSV)"
Deactivate
```

If this import fails, check dependency metadata and package exports before
publishing the next version.

## 7. Upload Later

TestPyPI first when dependency metadata changed:

```powershell
python -m twine upload --repository testpypi dist\*
```

PyPI release:

```powershell
python -m twine upload dist\*
```

Do not upload from this checklist until dependencies, version and smoke test are
confirmed.
