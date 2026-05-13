import sys
from pathlib import Path

_EVALS = Path(__file__).resolve().parents[1]
_REPO = _EVALS.parent

for _p in (_EVALS, _EVALS / "lib", _REPO / "backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
