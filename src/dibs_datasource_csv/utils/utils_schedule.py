import pandas as pd


def get_schedule_name(row: pd.DataFrame) -> str:
    """Extract the occupancy schedule name from an assignment row."""
    return row["schedule_name"].to_string(index=False).strip()
