"""Entry-point launcher for autochange.

This indirection allows us to ensure the package is importable even in rare
situations where editable installation .pth processing is skipped (observed
on some Python 3.13 environments). The code is intentionally tiny: if the
import fails we append the project ``src`` directory relative to this file.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path


def _ensure_path() -> None:
    # Fast path: if already importable do nothing
    try:
        import autochange  # noqa: F401
        return
    except Exception:
        pass
    # Attempt to locate project root using dist-info direct_url.json
    try:
        import importlib.metadata as md
        dist = md.distribution('autochange')
        direct = Path(dist.locate_file('direct_url.json'))
        if direct.exists():
            import json
            data = json.loads(direct.read_text())
            url = data.get('url', '')
            if url.startswith('file://'):
                root = Path(url.replace('file://',''))
                candidate_src = root / 'src'
                pkg_dir = candidate_src / 'autochange'
                if pkg_dir.is_dir() and str(candidate_src) not in sys.path:
                    sys.path.insert(0, str(candidate_src))
    except Exception:
        # Fallback: relative to this file
        project_root = Path(__file__).resolve().parent
        candidate_src = project_root
        if (candidate_src / 'autochange').is_dir() and str(candidate_src) not in sys.path:
            sys.path.insert(0, str(candidate_src))


def main() -> int:
    _ensure_path()
    from autochange.cli import app  # import after path fix
    return app()


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
