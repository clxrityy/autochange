"""Ensure src path is on sys.path for editable execution edge cases.

Some Python 3.13 environments with PEP 660 editable installs + pyproject only
may execute `python -m autochange.cli` from outside the project root without
processing the generated .pth early enough. As a defensive measure we inject
the project `src` directory if the top-level package can't be imported.
"""
from __future__ import annotations
import sys, os

PROJECT_ROOT_MARKERS = {"pyproject.toml", ".git"}

def _find_project_root(start: str) -> str | None:
    cur = os.path.abspath(start)
    for _ in range(10):  # bounded upward search
        if any(os.path.exists(os.path.join(cur, m)) for m in PROJECT_ROOT_MARKERS):
            if os.path.isdir(os.path.join(cur, "src")):
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None

try:
    import autochange  # noqa: F401
except Exception:
    root = _find_project_root(os.getcwd())
    if root:
        src = os.path.join(root, "src")
        if src not in sys.path:
            sys.path.insert(0, src)
            try:
                import autochange  # noqa: F401
            except Exception:
                pass
