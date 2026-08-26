"""Shared configuration for the DyBenchEval experiment scripts.

The historical scripts still use several legacy absolute paths. New code should
prefer these environment-backed paths so the repository can run on another
machine without editing source files.
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "data"
ORIG_ROOT = Path(os.environ.get("DYBENCH_ROOT", str(PROJECT_ROOT.parent)))
RAW_DATASETS = Path(os.environ.get("DYBENCH_RAW", str(ORIG_ROOT / "all_datasets")))
API_BASE = os.environ.get("DYBENCH_API_BASE", "https://api.whatai.cc/v1")
API_KEY = os.environ.get("DYBENCH_API_KEY", "")


def check_paths() -> None:
    """Print a concise environment and input-path diagnostic."""

    print("PROJECT_ROOT:", PROJECT_ROOT)
    print("DATA_ROOT   :", DATA_ROOT, "(present)" if DATA_ROOT.exists() else "(missing)")
    print("ORIG_ROOT   :", ORIG_ROOT, "(present)" if ORIG_ROOT.exists() else "(missing)")
    print("RAW_DATASETS:", RAW_DATASETS, "(present)" if RAW_DATASETS.exists() else "(missing)")
    print("API_BASE    :", API_BASE)
    print("API_KEY     :", "(set)" if API_KEY else "(not set; required for API scripts)")


if __name__ == "__main__":
    check_paths()

