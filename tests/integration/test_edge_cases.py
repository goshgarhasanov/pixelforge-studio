"""Edge-case və integrasiya testləri.

Bu testlər real fayllar üzərində bütöv pipeline-i icra edir və
çətin ssenariləri (zədəli fayl, alfa kanal, böyük şəkil, çoxlu format)
yoxlayır.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from pixelforge.core.models import Job, JobStatus, ResizeMode, ResizeOptions
from pixelforge.core.pipeline import make_default_options, process_job
from pixelforge.utils.formats import SUPPORTED_OUTPUT_FORMATS


def _make_image(path: Path, size: tuple[int, int], mode: str = "RGB", color: object = "blue") -> None:
    """Test üçün şəkil yaradır."""
    img = Image.new(mode, size, color)  # type: ignore[arg-type]
    fmt = path.suffix.lstrip(".").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    img.save(path, format=fmt)


@pytest.mark.parametrize("output_fmt", list(SUPPORTED_OUTPUT_FORMATS))
def test_pipeline_all_output_formats(tmp_path: Path, output_fmt: str) -> None:
    """Pipeline bütün çıxış formatları üçün uğurla işləyir."""
    src = tmp_path / "src.jpg"
    _make_image(src, (1200, 800))

    opts = make_default_options(output_format=output_fmt, target_kb=300)
    opts.output_dir = tmp_path / "out"
    job = process_job(Job(source=src, options=opts))

    assert job.status == JobStatus.DONE, f"{output_fmt} uğursuz: {job.error}"
    assert job.output_path is not None
    assert job.output_path.exists()


def test_alpha_png_to_jpg_uses_background(tmp_path: Path) -> None:
    """RGBA PNG → JPG çevrildikdə şəffaflıq arxa fonla doldurulur."""
    src = tmp_path / "alpha.png"
    img = Image.new("RGBA", (400, 400), (200, 50, 100, 100))
    img.save(src)

    opts = make_default_options(output_format="JPG", target_kb=200)
    opts.output_dir = tmp_path / "out"
    job = process_job(Job(source=src, options=opts))

    assert job.status == JobStatus.DONE
    out = Image.open(job.output_path)  # type: ignore[arg-type]
    assert out.mode == "RGB"


def test_corrupted_image_fails_gracefully(tmp_path: Path) -> None:
    """Zədəli (rastgələ bayt) fayl xəta ilə bitir, yox tətbiq çökmür."""
    src = tmp_path / "broken.jpg"
    src.write_bytes(b"NOT_A_REAL_IMAGE_FILE_AT_ALL_xxxx" * 50)

    opts = make_default_options()
    opts.output_dir = tmp_path / "out"
    job = process_job(Job(source=src, options=opts))

    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert job.error_traceback is not None


def test_unsupported_extension_fails(tmp_path: Path) -> None:
    """Dəstəklənməyən uzantı `FAILED` ilə bitir."""
    src = tmp_path / "data.txt"
    src.write_text("Bu sekil deyil", encoding="utf-8")

    opts = make_default_options()
    opts.output_dir = tmp_path / "out"
    job = process_job(Job(source=src, options=opts))

    assert job.status == JobStatus.FAILED
    assert "format" in (job.error or "").lower() or "dəstəklənmir" in (job.error or "").lower()


def test_resize_then_compress(tmp_path: Path) -> None:
    """Resize + compress birgə işləyir və hədəf qarşılanır."""
    src = tmp_path / "big.jpg"
    _make_image(src, (3000, 2000))

    opts = make_default_options(output_format="JPG", target_kb=100)
    opts.resize = ResizeOptions(mode=ResizeMode.LONG_EDGE, edge_pixels=1280)
    opts.output_dir = tmp_path / "out"

    job = process_job(Job(source=src, options=opts))

    assert job.status == JobStatus.DONE
    assert job.final_size <= int(100 * 1024 * 1.05)
    out = Image.open(job.output_path)  # type: ignore[arg-type]
    # Uzun tərəf təxminən 1280 olmalıdır.
    assert max(out.size) <= 1280


def test_output_filename_collision_increments(tmp_path: Path) -> None:
    """Eyni adlı fayl varsa, suffix əlavə olunur."""
    src1 = tmp_path / "photo.jpg"
    src2 = tmp_path / "duplicate" / "photo.jpg"
    src2.parent.mkdir()
    _make_image(src1, (800, 600))
    _make_image(src2, (800, 600))

    out_dir = tmp_path / "out"
    opts = make_default_options()
    opts.output_dir = out_dir

    job1 = process_job(Job(source=src1, options=opts))
    job2 = process_job(Job(source=src2, options=opts))

    assert job1.output_path != job2.output_path
    assert job2.output_path is not None
    assert "_" in job2.output_path.stem  # photo_1.jpg


def test_extreme_target_falls_back_to_smallest(tmp_path: Path) -> None:
    """Ağıl-üstü kiçik hədəf (1 KB) — alqoritm hələ də fayl qaytarır, status DONE."""
    src = tmp_path / "src.jpg"
    _make_image(src, (4000, 3000))

    opts = make_default_options(output_format="JPG", target_kb=1)
    opts.output_dir = tmp_path / "out"

    job = process_job(Job(source=src, options=opts))

    # Hədəf qarşılanmasa belə, fayl yaradılır (warning ilə).
    assert job.status == JobStatus.DONE
    assert job.output_path is not None
    assert job.output_path.exists()
