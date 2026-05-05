"""Tətbiqin giriş nöqtəsi: `python -m pixelforge`."""

from __future__ import annotations

import sys


def main() -> int:
    """Tətbiqi işə salır və qaytarış kodu verir."""
    # UI burada birbaşa import olunur — startup zamanını qısaltmaq üçün.
    from pixelforge.app import run_app

    return run_app(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
