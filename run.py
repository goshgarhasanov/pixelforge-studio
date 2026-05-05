"""Quraşdırma olmadan tətbiqi işə salmaq üçün asan başladıcı.

İstifadəsi:  `python run.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

# `src/` qovluğunu Python yoluna əlavə edirik.
SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pixelforge.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
