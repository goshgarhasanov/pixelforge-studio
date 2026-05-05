"""README üçün skripted şəkildə screenshot çəkir.

UI-ni başladır, müxtəlif vəziyyətlərdə doldurur, sonra PIL.ImageGrab ilə
ekran şəklini çəkib `assets/screenshots/` qovluğuna PNG kimi yazır.

İcra:  `python scripts/take_screenshots.py`
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# `src/`-i yola əlavə edirik.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageGrab  # noqa: E402

from pixelforge.core.models import Job, JobStatus  # noqa: E402
from pixelforge.logger import setup_logging  # noqa: E402
from pixelforge.ui.main_window import MainWindow  # noqa: E402

OUT_DIR = ROOT / "assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Test üçün hazır şəkillər generasiya edirik.
TMP_DIR = ROOT / "output" / "_screenshot_tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)


def _make_sample_images() -> list[Path]:
    """Növbəyə əlavə etmək üçün nümunə fayllar yaradır."""
    samples = [
        ("hero-banner.jpg", (2400, 1600), "JPEG", (52, 99, 220)),
        ("avatar.png", (800, 800), "PNG", (220, 80, 140)),
        ("product-shot.webp", (1920, 1280), "WEBP", (40, 180, 90)),
        ("logo.gif", (512, 512), "GIF", (245, 158, 11)),
        ("portrait.jpg", (3000, 4000), "JPEG", (140, 60, 200)),
        ("icon-source.png", (1024, 1024), "PNG", (10, 200, 220)),
    ]
    paths: list[Path] = []
    for name, size, fmt, color in samples:
        p = TMP_DIR / name
        if not p.exists():
            img = Image.new("RGB", size, color)
            img.save(p, format=fmt, quality=92)
        paths.append(p)
    return paths


def _capture(window: MainWindow, name: str) -> None:
    """Pəncərənin şəklini çəkib diskə yazır."""
    window.update_idletasks()
    window.update()
    # Pəncərənin tam screen-ə görə koordinatları.
    x = window.winfo_rootx()
    y = window.winfo_rooty()
    w = window.winfo_width()
    h = window.winfo_height()
    bbox = (x, y, x + w, y + h)
    img = ImageGrab.grab(bbox=bbox)
    out_path = OUT_DIR / name
    img.save(out_path, format="PNG", optimize=True)
    print(f"  [OK] {out_path.name}  ({w}x{h})")


def main() -> int:
    """Bütün screenshot ssenarilərini icra edir."""
    setup_logging(level=logging.INFO)
    log = logging.getLogger("screenshots")

    samples = _make_sample_images()
    print(f"Generated {len(samples)} sample images")

    app = MainWindow()
    # Pəncərəni ön plana çıxarmağa çalışırıq.
    app.lift()
    app.attributes("-topmost", True)
    app.update()
    app.attributes("-topmost", False)

    # ---- 1) İlkin (boş) vəziyyət ----
    app.after(800, lambda: _capture(app, "01-empty.png"))

    # ---- 2) Növbə dolu, hələ emal başlamayıb ----
    def fill_queue() -> None:
        app._add_files(samples)  # noqa: SLF001
        app.after(300, lambda: _capture(app, "02-queue-loaded.png"))

    app.after(1500, fill_queue)

    # ---- 3) Loglar görünür (səviyyəli mesajlar göndəririk) ----
    def emit_logs() -> None:
        log = logging.getLogger("pixelforge.demo")
        log.info("Toplu emal demo üçün başladı")
        log.info("hero-banner.jpg → JPG (200 KB hədəfi)")
        log.warning("portrait.jpg üçün ölçü kiçildilir")
        log.info("avatar.png → keyfiyyət 78")
        log.error("logo.gif: nümunə xəta — dəstəklənməyən kombinasiya")
        log.info("product-shot.webp → 187 KB (saved 92%)")
        log.critical("Demo: kritik səviyyə görüntülənir")
        log.info("icon-source.png → 145 KB (saved 78%)")
        app.after(400, lambda: _capture(app, "03-logs-active.png"))

    app.after(2400, emit_logs)

    # ---- 4) Bəzi işləri uğurlu / uğursuz vəziyyətdə nümayiş etdir ----
    def simulate_states() -> None:
        jobs = app._file_queue.jobs()  # noqa: SLF001
        if jobs:
            for i, job in enumerate(jobs):
                if i == 4:
                    job.status = JobStatus.FAILED
                    job.error = "Şəkil zədəlidir və oxuna bilmir."
                    job.error_suggestion = (
                        "Faylı başqa proqramda açıb yoxlayın və ya yenidən endirin."
                    )
                    job.error_traceback = (
                        "Traceback (most recent call last):\n"
                        '  File "compressor.py", line 87, in compress_to_target\n'
                        "    image.load()\n"
                        "PIL.UnidentifiedImageError: cannot identify image file 'portrait.jpg'\n"
                    )
                else:
                    job.status = JobStatus.DONE
                    job.final_size = max(50_000, job.original_size // 8)
                app._file_queue.refresh_job(i)
            total_saved = sum(j.saved_bytes for j in jobs)
            app._status_bar.set_saved(total_saved)  # noqa: SLF001
            app._status_bar.set_status("status.done")  # noqa: SLF001
        app.after(400, lambda: _capture(app, "04-results.png"))

    app.after(3400, simulate_states)

    # ---- 5) Xəta dialoqu ----
    def show_error_dialog() -> None:
        from pixelforge.ui.widgets.error_dialog import show_error

        show_error(
            app,
            title="Şəkil emal edilə bilmədi",
            message="portrait.jpg faylı zədəlidir və açıla bilmir.",
            suggestion="Faylı başqa şəkil görüntüləyicidə açıb yoxlayın və ya yenidən endirin.",
            traceback_text=(
                "Traceback (most recent call last):\n"
                '  File "src/pixelforge/core/pipeline.py", line 64, in process_job\n'
                "    image.load()\n"
                '  File "PIL/ImageFile.py", line 282, in load\n'
                "    raise OSError(\n"
                "PIL.UnidentifiedImageError: cannot identify image file 'portrait.jpg'\n"
            ),
            affected_files=["output/_screenshot_tmp/portrait.jpg"],
        )
        # Bir az gözləyirik ki dialog tam görünsün.
        app.after(800, lambda: _capture(app, "05-error-dialog.png"))

    app.after(4400, show_error_dialog)

    # ---- 6) Pəncərə bağlanması ----
    app.after(5800, app._on_close)  # noqa: SLF001

    app.mainloop()

    print(f"\nAll screenshots saved to: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
