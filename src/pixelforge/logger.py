"""Tətbiq üçün loglama sistemini qurur.

İki çıxış yolu var:
  1. Konsol (stderr) — INFO və yuxarı.
  2. Fırlanan fayl (`logs/pixelforge.log`) — DEBUG və yuxarı, 5 MB × 5 yedək.

UI-də canlı log görüntüsü üçün `QueueLogHandler` istifadə olunur — fon
thread-lərindən gələn loglar UI tərəfindən təhlükəsiz şəkildə oxuna bilir.
"""

from __future__ import annotations

import logging
import queue
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pixelforge.utils.paths import logs_dir

LOG_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)-30s — %(message)s"
DATE_FORMAT = "%H:%M:%S"

# UI-nin oxuyacağı global log növbəsi.
_ui_queue: queue.Queue[str] = queue.Queue(maxsize=5000)


class QueueLogHandler(logging.Handler):
    """Log qeydlərini bir növbəyə göndərir — UI tərəfindən oxunmaq üçün."""

    def __init__(self, q: queue.Queue[str]) -> None:
        super().__init__(level=logging.INFO)
        self._queue = q

    def emit(self, record: logging.LogRecord) -> None:
        """Bir qeydi formatlayıb növbəyə əlavə edir."""
        try:
            msg = self.format(record)
        except Exception:
            return
        try:
            self._queue.put_nowait(msg)
        except queue.Full:
            # Növbə doludur — köhnə qeydləri silirik.
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(msg)
            except (queue.Empty, queue.Full):
                pass


def get_ui_log_queue() -> queue.Queue[str]:
    """UI-nin abunə olacağı log növbəsini qaytarır."""
    return _ui_queue


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Loglama infrastrukturunu qurur və kök logger-i qaytarır.

    İdempotentdir — təkrar çağırılsa, mövcud handler-lər silinir.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Mövcud handler-ləri təmizləyirik (test mühitləri üçün vacib).
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1) Konsol handler.
    # Windows konsolunda Azərbaycan simvollarını düzgün göstərmək üçün
    # stderr-i UTF-8 ilə yenidən konfiqurasiya edirik.
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass
    console = logging.StreamHandler(stream=sys.stderr)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 2) Fırlanan fayl handler.
    log_path = logs_dir() / "pixelforge.log"
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 3) UI növbəsi.
    queue_handler = QueueLogHandler(_ui_queue)
    queue_handler.setFormatter(formatter)
    root.addHandler(queue_handler)

    # Uncaught exception-ları faylda saxlayırıq.
    def _excepthook(exc_type: type[BaseException], exc: BaseException, tb: object) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)  # type: ignore[arg-type]
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        crash_path = logs_dir() / f"crash-{ts}.log"
        logging.getLogger("pixelforge").critical(
            "Gözlənilməz xəta — qeyd %s faylına yazıldı", crash_path
        )
        try:
            import traceback

            crash_path.write_text(
                "".join(traceback.format_exception(exc_type, exc, tb)),  # type: ignore[arg-type]
                encoding="utf-8",
            )
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)  # type: ignore[arg-type]

    sys.excepthook = _excepthook

    logger = logging.getLogger("pixelforge")
    logger.info("Loglama hazırdır — fayl: %s", log_path)
    return logger
