"""Golden regression runner for DibsDataSourceCSV against a local DIBS core.

Usage from the DibsDataSourceCSV root:

    python scripts/regression_csv_golden.py --update-golden
    python scripts/regression_csv_golden.py
    python scripts/regression_csv_golden.py --benchmark-cache

The first command creates/updates the golden CSV files. The second command runs
DIBS.multi() again with the local DataSourceCSV package and compares all
SummaryResult fields plus selected hourly values. The benchmark command runs a
cold and warm simulation on the same DataSourceCSV instance to show cache impact.
"""

from __future__ import annotations

import argparse
import math
import sys
from numbers import Real
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SRC = PROJECT_ROOT / "src"
STAND_DIBS_ROOT = PROJECT_ROOT.parent
DEFAULT_INPUT = STAND_DIBS_ROOT / "SimulationData_Breitenerhebung.csv"
DEFAULT_DIBS_CORE_ROOT = STAND_DIBS_ROOT / "DibsComputingCore"
DEFAULT_DIBS_CORE_SRC = DEFAULT_DIBS_CORE_ROOT / "src"
DEFAULT_DIBS_DATA_SRC = STAND_DIBS_ROOT / "DibsData" / "src"
DEFAULT_EXPECTED_CORE_BRANCH = "dibscc_error_handling"
DEFAULT_GOLDEN = PROJECT_ROOT / "tests" / "golden" / "datasourcecsv_summary_9_buildings.csv"
DEFAULT_HOURLY_GOLDEN = PROJECT_ROOT / "tests" / "golden" / "datasourcecsv_hourly_sample_9_buildings.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "regression_results"
HOURLY_SAMPLE_HOURS = (0, 1, 8, 12, 18, 8759)
HOURLY_SAMPLE_FIELDS = (
    "heating_demand",
    "cooling_demand",
    "all_hot_water_demand",
    "temp_air",
    "outside_temp",
    "lighting_demand",
    "internal_gains",
    "solar_gains_total",
)


def _prepend_source_path(path: Path) -> None:
    if path.exists():
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def _read_git_branch(repo_root: Path) -> str | None:
    """Read the current branch without invoking git.

    This avoids Windows/sandbox `safe.directory` issues while still protecting
    the regression from accidentally running against the wrong core branch.
    """
    git_path = repo_root / ".git"
    if git_path.is_file():
        content = git_path.read_text(encoding="utf-8").strip()
        if content.startswith("gitdir:"):
            git_path = (repo_root / content.split(":", 1)[1].strip()).resolve()
    head_path = git_path / "HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="utf-8").strip()
    if head.startswith("ref: refs/heads/"):
        return head.removeprefix("ref: refs/heads/")
    return head[:12] if head else None


def _validate_core_branch(core_root: Path, expected_branch: str, skip_check: bool) -> int:
    if skip_check:
        return 0
    current_branch = _read_git_branch(core_root)
    if current_branch == expected_branch:
        return 0
    print(f"core_branch_expected={expected_branch}")
    print(f"core_branch_current={current_branch or '<unknown>'}")
    print("Switch DibsComputingCore to the expected branch or pass --skip-core-branch-check.")
    return 3


def _normalize_cell(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return value[0] if len(value) == 1 else str(value)
    return value


def _summary_dataframe(summaries: list[Any]) -> pd.DataFrame:
    rows = []
    for summary in summaries:
        rows.append({key: _normalize_cell(value) for key, value in vars(summary).items()})
    dataframe = pd.DataFrame(rows)
    if "building_id" in dataframe.columns:
        dataframe = dataframe.sort_values("building_id").reset_index(drop=True)
    return dataframe


def _hourly_sample_dataframe(results: list[Any], summaries: list[Any]) -> pd.DataFrame:
    rows = []
    building_ids = [
        getattr(summary, "building_id", index) for index, summary in enumerate(summaries)
    ]
    for building_index, result in enumerate(results):
        building_id = building_ids[building_index]
        for hour in HOURLY_SAMPLE_HOURS:
            row = {"building_id": building_id, "hour": hour}
            for field in HOURLY_SAMPLE_FIELDS:
                values = getattr(result, field)
                row[field] = values[hour]
            rows.append(row)
    dataframe = pd.DataFrame(rows)
    if not dataframe.empty:
        dataframe = dataframe.sort_values(["building_id", "hour"]).reset_index(drop=True)
    return dataframe


def _prepare_import_paths(dibs_core_src: Path, dibs_data_src: Path) -> None:
    # Prepend in dependency order so local DataSourceCSV wins over installed packages.
    _prepend_source_path(dibs_data_src)
    _prepend_source_path(dibs_core_src)
    _prepend_source_path(PROJECT_SRC)


def _create_datasource(input_csv: Path):
    from dibs_datasource_csv.datasource_csv import DataSourceCSV

    return DataSourceCSV(
        str(input_csv),
        "din18599",
        "mid",
        "sia2024",
        "2004-2018",
        "GEG",
    )


def _run_dibs_with_datasource(datasource) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    from dibs_computing_core.iso_simulator.dibs.dibs import DIBS

    start = perf_counter()
    simulation_time_s, hourly_results, summaries = DIBS(datasource).multi()
    wall_time_s = perf_counter() - start
    return (
        _summary_dataframe(summaries),
        _hourly_sample_dataframe(hourly_results, summaries),
        simulation_time_s,
        wall_time_s,
    )


def _run_simulation(
    input_csv: Path,
    dibs_core_src: Path,
    dibs_data_src: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    _prepare_import_paths(dibs_core_src, dibs_data_src)
    return _run_dibs_with_datasource(_create_datasource(input_csv))


def _values_equal(golden_value: Any, current_value: Any, tolerance: float) -> bool:
    if pd.isna(golden_value) and pd.isna(current_value):
        return True
    if isinstance(golden_value, Real) and isinstance(current_value, Real):
        return math.isclose(
            float(golden_value),
            float(current_value),
            rel_tol=tolerance,
            abs_tol=tolerance,
        )
    return str(golden_value) == str(current_value)


def _abs_diff(left: Any, right: Any) -> float | None:
    if isinstance(left, Real) and isinstance(right, Real):
        if pd.isna(left) or pd.isna(right):
            return None
        return abs(float(left) - float(right))
    return None


def _compare(golden: pd.DataFrame, current: pd.DataFrame, tolerance: float) -> pd.DataFrame:
    diff_rows = []
    golden_columns = list(golden.columns)
    current_columns = list(current.columns)

    for column in sorted(set(golden_columns) - set(current_columns)):
        diff_rows.append(
            {"building_id": None, "field": column, "problem": "missing_in_current"}
        )
    for column in sorted(set(current_columns) - set(golden_columns)):
        diff_rows.append(
            {"building_id": None, "field": column, "problem": "new_in_current"}
        )

    shared_columns = [column for column in golden_columns if column in current_columns]
    row_count = min(len(golden), len(current))

    if len(golden) != len(current):
        diff_rows.append(
            {
                "building_id": None,
                "field": "<row_count>",
                "problem": "row_count_changed",
                "golden_value": len(golden),
                "current_value": len(current),
            }
        )

    for index in range(row_count):
        building_id = current.iloc[index].get("building_id", index)
        hour = current.iloc[index].get("hour", None)
        for column in shared_columns:
            golden_value = golden.iloc[index][column]
            current_value = current.iloc[index][column]
            if _values_equal(golden_value, current_value, tolerance):
                continue
            diff_rows.append(
                {
                    "building_id": building_id,
                    "hour": hour,
                    "field": column,
                    "problem": "value_changed",
                    "golden_value": golden_value,
                    "current_value": current_value,
                    "abs_diff": _abs_diff(golden_value, current_value),
                }
            )
    return pd.DataFrame(diff_rows)


def _write_cache_benchmark_output(
    output_dir: Path,
    cold_summary: pd.DataFrame,
    warm_summary: pd.DataFrame,
    summary_diff: pd.DataFrame,
    cold_hourly: pd.DataFrame,
    warm_hourly: pd.DataFrame,
    hourly_diff: pd.DataFrame,
    cold_simulation_time_s: float,
    warm_simulation_time_s: float,
    cold_wall_time_s: float,
    warm_wall_time_s: float,
    tolerance: float,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "datasourcecsv_cache_benchmark.xlsx"
    wall_delta_s = cold_wall_time_s - warm_wall_time_s
    wall_speedup = cold_wall_time_s / warm_wall_time_s if warm_wall_time_s else None
    metadata = pd.DataFrame(
        {
            "property": [
                "buildings",
                "fields",
                "hourly_rows",
                "summary_differences",
                "hourly_differences",
                "differences",
                "cold_simulation_time_s",
                "warm_simulation_time_s",
                "cold_wall_time_s",
                "warm_wall_time_s",
                "wall_delta_s",
                "wall_speedup",
                "tolerance",
            ],
            "value": [
                len(cold_summary),
                len(cold_summary.columns),
                len(cold_hourly),
                len(summary_diff),
                len(hourly_diff),
                len(summary_diff) + len(hourly_diff),
                cold_simulation_time_s,
                warm_simulation_time_s,
                cold_wall_time_s,
                warm_wall_time_s,
                wall_delta_s,
                wall_speedup,
                tolerance,
            ],
        }
    )
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        metadata.to_excel(writer, sheet_name="Metadata", index=False)
        cold_summary.to_excel(writer, sheet_name="ColdSummary", index=False)
        warm_summary.to_excel(writer, sheet_name="WarmSummary", index=False)
        summary_diff.to_excel(writer, sheet_name="SummaryDiff", index=False)
        cold_hourly.to_excel(writer, sheet_name="ColdHourly", index=False)
        warm_hourly.to_excel(writer, sheet_name="WarmHourly", index=False)
        hourly_diff.to_excel(writer, sheet_name="HourlyDiff", index=False)
    return output_file


def _run_cache_benchmark(
    input_csv: Path,
    dibs_core_src: Path,
    dibs_data_src: Path,
    output_dir: Path,
    tolerance: float,
) -> int:
    _prepare_import_paths(dibs_core_src, dibs_data_src)
    datasource = _create_datasource(input_csv)

    cold_summary, cold_hourly, cold_sim_time_s, cold_wall_time_s = (
        _run_dibs_with_datasource(datasource)
    )
    warm_summary, warm_hourly, warm_sim_time_s, warm_wall_time_s = (
        _run_dibs_with_datasource(datasource)
    )

    summary_diff = _compare(cold_summary, warm_summary, tolerance)
    hourly_diff = _compare(cold_hourly, warm_hourly, tolerance)
    output_file = _write_cache_benchmark_output(
        output_dir,
        cold_summary,
        warm_summary,
        summary_diff,
        cold_hourly,
        warm_hourly,
        hourly_diff,
        cold_sim_time_s,
        warm_sim_time_s,
        cold_wall_time_s,
        warm_wall_time_s,
        tolerance,
    )

    total_differences = len(summary_diff) + len(hourly_diff)
    wall_delta_s = cold_wall_time_s - warm_wall_time_s
    wall_speedup = cold_wall_time_s / warm_wall_time_s if warm_wall_time_s else 0.0
    print(
        f"cache_benchmark cold_wall_time_s={cold_wall_time_s:.6f} "
        f"warm_wall_time_s={warm_wall_time_s:.6f} "
        f"delta_s={wall_delta_s:.6f} speedup={wall_speedup:.3f}"
    )
    print(
        f"cache_benchmark cold_simulation_time_s={cold_sim_time_s:.6f} "
        f"warm_simulation_time_s={warm_sim_time_s:.6f}"
    )
    print(
        f"cache_benchmark differences={total_differences} "
        f"summary_differences={len(summary_diff)} hourly_differences={len(hourly_diff)}"
    )
    print(f"cache_benchmark_file={output_file}")
    return 0 if summary_diff.empty and hourly_diff.empty else 1


def _write_outputs(
    output_dir: Path,
    current: pd.DataFrame,
    diff: pd.DataFrame,
    hourly_current: pd.DataFrame,
    hourly_diff: pd.DataFrame,
    simulation_time_s: float,
    wall_time_s: float,
    tolerance: float,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "datasourcecsv_9_buildings_comparison.xlsx"
    metadata = pd.DataFrame(
        {
            "property": [
                "buildings",
                "fields",
                "summary_differences",
                "hourly_differences",
                "differences",
                "hourly_rows",
                "simulation_time_s",
                "wall_time_s",
                "tolerance",
            ],
            "value": [
                len(current),
                len(current.columns),
                len(diff),
                len(hourly_diff),
                len(diff) + len(hourly_diff),
                len(hourly_current),
                simulation_time_s,
                wall_time_s,
                tolerance,
            ],
        }
    )
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        metadata.to_excel(writer, sheet_name="Metadata", index=False)
        current.to_excel(writer, sheet_name="Current", index=False)
        diff.to_excel(writer, sheet_name="Diff", index=False)
        hourly_current.to_excel(writer, sheet_name="HourlyCurrent", index=False)
        hourly_diff.to_excel(writer, sheet_name="HourlyDiff", index=False)
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run and compare the DataSourceCSV 9-building golden regression."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--dibs-core-root", type=Path, default=DEFAULT_DIBS_CORE_ROOT)
    parser.add_argument("--dibs-core-src", type=Path, default=DEFAULT_DIBS_CORE_SRC)
    parser.add_argument("--dibs-data-src", type=Path, default=DEFAULT_DIBS_DATA_SRC)
    parser.add_argument("--expected-core-branch", default=DEFAULT_EXPECTED_CORE_BRANCH)
    parser.add_argument("--skip-core-branch-check", action="store_true")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--hourly-golden", type=Path, default=DEFAULT_HOURLY_GOLDEN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--update-golden", action="store_true")
    parser.add_argument(
        "--benchmark-cache",
        action="store_true",
        help="Run cold and warm simulations on the same DataSourceCSV instance.",
    )
    args = parser.parse_args()

    branch_status = _validate_core_branch(
        args.dibs_core_root, args.expected_core_branch, args.skip_core_branch_check
    )
    if branch_status != 0:
        return branch_status

    if args.benchmark_cache:
        return _run_cache_benchmark(
            args.input,
            args.dibs_core_src,
            args.dibs_data_src,
            args.output_dir,
            args.tolerance,
        )

    current, hourly_current, simulation_time_s, wall_time_s = _run_simulation(
        args.input,
        args.dibs_core_src,
        args.dibs_data_src,
    )

    if args.update_golden:
        args.golden.parent.mkdir(parents=True, exist_ok=True)
        args.hourly_golden.parent.mkdir(parents=True, exist_ok=True)
        current.to_csv(args.golden, index=False)
        hourly_current.to_csv(args.hourly_golden, index=False)
        print(f"golden_updated={args.golden}")
        print(f"hourly_golden_updated={args.hourly_golden}")
        print(
            f"buildings={len(current)} fields={len(current.columns)} "
            f"hourly_rows={len(hourly_current)} "
            f"simulation_time_s={simulation_time_s:.6f} wall_time_s={wall_time_s:.6f}"
        )
        return 0

    missing_goldens = [
        path for path in (args.golden, args.hourly_golden) if not path.exists()
    ]
    if missing_goldens:
        for missing_golden in missing_goldens:
            print(f"golden_missing={missing_golden}")
        print("Create them first with: python scripts/regression_csv_golden.py --update-golden")
        return 2

    golden = pd.read_csv(args.golden, keep_default_na=False)
    hourly_golden = pd.read_csv(args.hourly_golden, keep_default_na=False)
    diff = _compare(golden, current, args.tolerance)
    hourly_diff = _compare(hourly_golden, hourly_current, args.tolerance)
    output_file = _write_outputs(
        args.output_dir,
        current,
        diff,
        hourly_current,
        hourly_diff,
        simulation_time_s,
        wall_time_s,
        args.tolerance,
    )

    total_differences = len(diff) + len(hourly_diff)
    print(
        f"buildings={len(current)} fields={len(current.columns)} "
        f"hourly_rows={len(hourly_current)} differences={total_differences}"
    )
    print(f"summary_differences={len(diff)} hourly_differences={len(hourly_diff)}")
    print(f"simulation_time_s={simulation_time_s:.6f} wall_time_s={wall_time_s:.6f}")
    print(f"comparison_file={output_file}")
    return 0 if diff.empty and hourly_diff.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
