"""Tətbiqin başlatma (bootstrap) modulu."""

from __future__ import annotations

import logging
from typing import Sequence

from pixelforge import __app_name__, __version__
from pixelforge.config import load_config
from pixelforge.i18n import set_language
from pixelforge.logger import setup_logging

logger = logging.getLogger(__name__)


def run_app(_argv: Sequence[str]) -> int:
    """Tətbiqi qurur və UI əsas döngüsünü işə salır."""
    setup_logging(level=logging.INFO)
    cfg = load_config()
    set_language(cfg.language)

    logger.info("%s v%s işə salınır", __app_name__, __version__)

    # MainWindow yalnız UI başlandıqda import olunur — gec başlatma.
    from pixelforge.ui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()

    logger.info("%s bağlandı", __app_name__)
    return 0
