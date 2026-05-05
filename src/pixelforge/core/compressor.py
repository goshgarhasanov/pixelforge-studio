"""Hədəf ölçüyə qədər deterministik sıxışdırma alqoritmi.

Strategiya:
  1. EXIF rotasiyası tətbiq olunur.
  2. JPEG / WEBP keyfiyyəti binary search ilə tapılır (≤ 8 təkrar).
  3. Minimum keyfiyyətdə də ölçü hələ böyükdürsə, şəkil 95% addımla
     kiçildilir — qısa tərəf 320 pikseldən aşağı düşənə qədər.
  4. Nəticə bayt + hesabat şəklində qaytarılır.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Literal

from PIL import Image

from pixelforge.core.converter import prepare_for_format
from pixelforge.core.models import CompressionReport
from pixelforge.utils.exif import auto_orient
from pixelforge.utils.formats import normalize_format, to_pillow_format

logger = logging.getLogger(__name__)

# Maksimum binary search təkrar sayı.
MAX_QUALITY_ITERATIONS = 8


def _encode(image: Image.Image, fmt: str, quality: int) -> bytes:
    """Şəkli yaddaşda kodlayıb bayt qaytarır."""
    buf = BytesIO()
    pil_fmt = to_pillow_format(fmt)
    kwargs: dict[str, object] = {}
    if pil_fmt == "JPEG":
        kwargs.update(
            {
                "quality": int(quality),
                "optimize": True,
                "progressive": True,
                "subsampling": 2,
            }
        )
    elif pil_fmt == "WEBP":
        kwargs.update({"quality": int(quality), "method": 6})
    elif pil_fmt == "PNG":
        kwargs.update({"optimize": True, "compress_level": 9})
    image.save(buf, format=pil_fmt, **kwargs)
    return buf.getvalue()


def compress_to_target(
    image: Image.Image,
    target_kb: int = 200,
    fmt: Literal["JPEG", "JPG", "WEBP", "PNG"] = "JPEG",
    *,
    min_quality: int = 35,
    max_quality: int = 95,
    min_short_edge: int = 320,
    downscale_step: float = 0.95,
    tolerance: float = 1.02,
) -> tuple[bytes, CompressionReport]:
    """Şəkli `target_kb` kilobayta uyğun ölçüdə bayt formasında qaytarır.

    Geri qayıdan tuple: (bayt, hesabat).
    Tolerans 2% - hədəfi tam bərabər tutmaq əvəzinə yaxınlığa icazə verir.
    """
    if target_kb <= 0:
        raise ValueError("target_kb müsbət olmalıdır")

    fmt_norm = normalize_format(fmt)
    target_bytes = int(target_kb * 1024 * tolerance)

    # Hədəf format JPEG / WEBP deyilsə (məs. PNG), keyfiyyət döngüsü işləməz —
    # birbaşa kodlayıb downscale döngüsünə keçirik.
    is_quality_codec = fmt_norm in ("JPG", "WEBP")

    work = auto_orient(image.copy())
    work = prepare_for_format(work, fmt_norm)

    iterations = 0
    downscaled = False
    last_data: bytes = b""
    last_quality = max_quality

    while True:
        if is_quality_codec:
            # Binary search.
            lo, hi = min_quality, max_quality
            best_data: bytes | None = None
            best_q = max_quality
            for _ in range(MAX_QUALITY_ITERATIONS):
                iterations += 1
                q = (lo + hi) // 2
                data = _encode(work, fmt_norm, q)
                if len(data) <= target_bytes:
                    best_data = data
                    best_q = q
                    lo = q + 1
                else:
                    hi = q - 1
                if lo > hi:
                    break

            if best_data is not None:
                last_data = best_data
                last_quality = best_q
                logger.debug(
                    "Hədəf qarşılandı: %d bayt, keyfiyyət=%d, ölçü=%s",
                    len(best_data),
                    best_q,
                    work.size,
                )
                return best_data, CompressionReport(
                    final_quality=best_q,
                    final_width=work.size[0],
                    final_height=work.size[1],
                    final_bytes=len(best_data),
                    iterations=iterations,
                    downscaled=downscaled,
                    target_met=True,
                )

            # Minimum keyfiyyətdə belə hədəf qarşılanmadı — kiçildirik.
            last_data = _encode(work, fmt_norm, min_quality)
            last_quality = min_quality
        else:
            # PNG / digər itkisiz format — yalnız downscale ilə endirə bilərik.
            iterations += 1
            data = _encode(work, fmt_norm, max_quality)
            last_data = data
            last_quality = max_quality
            if len(data) <= target_bytes:
                return data, CompressionReport(
                    final_quality=max_quality,
                    final_width=work.size[0],
                    final_height=work.size[1],
                    final_bytes=len(data),
                    iterations=iterations,
                    downscaled=downscaled,
                    target_met=True,
                )

        # Kiçiltmə addımı.
        new_w = max(1, int(work.size[0] * downscale_step))
        new_h = max(1, int(work.size[1] * downscale_step))
        if min(new_w, new_h) < min_short_edge:
            # Daha kiçiltməyə dəyməz — son nəticəni qaytarırıq.
            logger.warning(
                "Hədəf qarşılanmadı, minimum tərəf həddinə çatdı: %s bayt",
                len(last_data),
            )
            return last_data, CompressionReport(
                final_quality=last_quality,
                final_width=work.size[0],
                final_height=work.size[1],
                final_bytes=len(last_data),
                iterations=iterations,
                downscaled=downscaled,
                target_met=False,
            )
        work = work.resize((new_w, new_h), Image.Resampling.LANCZOS)
        downscaled = True
