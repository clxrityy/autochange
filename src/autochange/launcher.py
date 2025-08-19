"""Launcher for the autochange CLI (package-internal).

Placed inside the package so normal package discovery handles it. Provides a
fallback to add the editable src path if .pth processing failed.
"""
from __future__ import annotations
import sys, os
from pathlib import Path

def _bootstrap_path():
    try:
        import autochange  # noqa: F401
        return
    except Exception:
        pass
    # editable fallback: look two levels up from this file for src
    here = Path(__file__).resolve()
    root = here.parent.parent  # src directory
    if root.is_dir() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main():
    _bootstrap_path()
    from .cli import app
    return app()

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
