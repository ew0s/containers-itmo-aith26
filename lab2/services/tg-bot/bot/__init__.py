from __future__ import annotations

import sys
from pathlib import Path


def _detect_project_root(marker: str = "shared") -> Path:
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        if (candidate / marker).exists():
            return candidate
    return current


LAB2_ROOT = _detect_project_root()
if str(LAB2_ROOT) not in sys.path:
    sys.path.append(str(LAB2_ROOT))

