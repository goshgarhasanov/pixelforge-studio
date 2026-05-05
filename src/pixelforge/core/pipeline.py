"""Tək bir şəkil üçün convert → resize → compress zəncirini icra edir."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image

from pixelforge.core.compressor import compress_to_target
from pixelforge.core.converter import encode_image, is_animated
from pixelforge.core.exceptions import (
    PixelForgeError,
    SourceNotFoundError,
    UnsupportedFormatError,
    classify_exception,
)
from pixelforge.core.models import (
    CompressionOptions,
    ConvertOptions,
    Job,
    JobOptions,
    JobStatus,
    ResizeMode,
    ResizeOptions,
)
from pixelforge.core.resizer import resize_image
from pixelforge.utils.formats import extension_for, is_supported_input, normalize_format
from pixelforge.utils.paths import output_dir

logger = logging.getLogger(__name__)

# HEIC / HEIF dəstəyini avtomatik qoşmağa çalışırıq (modulu yoxdursa keçirik).
try:  # pragma: no cover
    import pillow_heif  # type: ignore[import-not-found]

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass


def _build_output_path(source: Path, options: JobOptions) -> Path:
    """Çıxış faylının tam yolunu qurur (ad toqquşmalarına qarşı suffiks əlavə edir)."""
    out_dir = options.output_dir or output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = extension_for(options.convert.output_format)
    base = source.stem
    candidate = out_dir / f"{base}{ext}"
    counter = 1
    while candidate.exists():
        candidate = out_dir / f"{base}_{counter}{ext}"
        counter += 1
    return candidate


def process_job(job: Job) -> Job:
    """Verilmiş işi başdan-sona emal edir və nəticəni `Job`-a yazır."""
    started_at = time.perf_counter()
    job.status = JobStatus.RUNNING

    try:
        if not job.source.exists():
            raise SourceNotFoundError(f"Mənbə fayl tapılmadı: {job.source}")

        if not is_supported_input(job.source):
            raise UnsupportedFormatError(
                f"Format dəstəklənmir: {job.source.suffix or '<uzantısız>'}"
            )

        job.original_size = job.source.stat().st_size

        with Image.open(job.source) as image:
            image.load()

            if is_animated(image, job.options.convert.output_format):
                logger.info("Animasiyalı şəkil aşkar edildi: %s", job.source.name)

            # 1) Ölçü dəyişdirmə.
            resized = resize_image(image, job.options.resize)

            # 2) Format çevrilməsi və sıxışdırma.
            target_fmt = normalize_format(job.options.convert.output_format)

            if (
                job.options.compress.enabled
                and target_fmt in ("JPG", "WEBP", "PNG")
            ):
                # Hədəf ölçüyə qədər sıxışdırırıq.
                data, report = compress_to_target(
                    resized,
                    target_kb=job.options.compress.target_kb,
                    fmt=target_fmt,  # type: ignore[arg-type]
                    min_quality=job.options.compress.min_quality,
                    max_quality=job.options.compress.max_quality,
                    min_short_edge=job.options.compress.min_short_edge,
                )
                if not report.target_met:
                    logger.warning(
                        "Hədəf ölçüyə tam çatılmadı (%s): son ölçü %d bayt",
                        job.source.name,
                        report.final_bytes,
                    )
            else:
                # Sadə kodlaşdırma — sıxışdırma olmadan.
                data = encode_image(
                    resized,
                    target_fmt,
                    quality=job.options.compress.max_quality,
                    background=job.options.convert.background,
                    keep_metadata=job.options.convert.keep_metadata,
                )

        # 3) Diskə yazırıq.
        output_path = _build_output_path(job.source, job.options)
        output_path.write_bytes(data)

        job.output_path = output_path
        job.final_size = len(data)
        job.status = JobStatus.DONE
        logger.info(
            "✓ %s → %s (%d → %d bayt)",
            job.source.name,
            output_path.name,
            job.original_size,
            job.final_size,
        )

    except PixelForgeError as exc:
        # Tətbiqə xas xəta — istifadəçi mesajı ilə.
        import traceback as _tb

        job.status = JobStatus.FAILED
        job.error = exc.user_message
        job.error_suggestion = exc.suggestion
        job.error_traceback = _tb.format_exc()
        logger.error("✗ %s — %s", job.source.name, exc.user_message)
    except Exception as exc:  # noqa: BLE001 — UI-yə xəta mesajı ötürmək lazımdır.
        # Naməlum xətanı uyğun tipə çeviririk.
        import traceback as _tb

        classified = classify_exception(exc)
        job.status = JobStatus.FAILED
        job.error = classified.user_message
        job.error_suggestion = classified.suggestion
        job.error_traceback = _tb.format_exc()
        logger.exception("✗ %s — %s", job.source.name, classified.user_message)

    finally:
        job.duration_ms = int((time.perf_counter() - started_at) * 1000)

    return job


def make_default_options(
    output_format: str = "JPG",
    target_kb: int = 200,
    resize_mode: ResizeMode = ResizeMode.NONE,
) -> JobOptions:
    """Standart parametrlərlə yeni `JobOptions` qaytarır."""
    return JobOptions(
        convert=ConvertOptions(output_format=output_format),
        resize=ResizeOptions(mode=resize_mode),
        compress=CompressionOptions(target_kb=target_kb),
    )
