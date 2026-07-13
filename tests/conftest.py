"""Test path setup for local sibling repositories.

The package imports `dibs_data` and `dibs_computing_core` at module import time.
During local development these packages usually live as sibling repositories next
to `DibsDataSourceCSV`, so tests add their `src` folders explicitly.
"""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
STAND_DIBS_ROOT = REPO_ROOT.parent
SIBLING_SRC_PATHS = (
    STAND_DIBS_ROOT / "DibsData" / "src",
    STAND_DIBS_ROOT / "DibsComputingCore" / "src",
)

for path in reversed(SIBLING_SRC_PATHS):
    if path.exists():
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
