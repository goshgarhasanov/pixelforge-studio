"""Şəkil format çevrilməsi (JPG ↔ PNG ↔ WEBP ↔ GIF ↔ BMP ↔ TIFF ↔ ICO)."""

from __future__ import annotations

import logging
from io import BytesIO

from PIL import Image

from pixelforge.utils.exif import auto_orient
from pixelforge.utils.formats import (
    ANIMATION_FORMATS,
    normalize_format,
    supports_alpha,
    to_pillow_format,
)

logger = logging.getLogger(__name__)

# ICO çıxışı üçün standart ölçü dəstləri.
ICO_SIZES: tuple[tuple[int, int], ...] = (
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Hex rəng kodunu RGB üçlüyünə çevirir (məs. '#FFFFFF' → (255, 255, 255))."""
    s = hex_color.lstrip("#")
    if len(s) != 6:
        return (255, 255, 255)
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return (255, 255, 255)


def prepare_for_format(
    image: Image.Image,
    target_format: str,
    background: str = "#FFFFFF",
) -> Image.Image:
    """Şəkli hədəf format üçün hazırlayır (rəng rejimi, şəffaflıq).

    Şəffaflığı dəstəkləməyən format-lar üçün arxa fonu doldurur.
    Palet (P) və boz (L) rejimləri uyğun şəkildə RGB-yə çevrilir.
    """
    fmt = normalize_format(target_format)
    img = image

    # EXIF rotation tətbiq edilir.
    img = auto_orient(img)

    if supports_alpha(fmt):
        # Hədəf şəffaflığı dəstəkləyirsə, RGBA-ya keçid edirik.
        if img.mode not in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        elif img.mode == "P":
            img = img.convert("RGBA")
    else:
        # Hədəf şəffaflığı dəstəkləmirsə, alfa kanalını arxa fona qarışdırırıq.
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, _hex_to_rgb(background))
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

    return img


def encode_image(
    image: Image.Image,
    target_format: str,
    *,
    quality: int = 90,
    background: str = "#FFFFFF",
    keep_metadata: bool = False,
) -> bytes:
    """Şəkli verilmiş format kodlarına uyğun bayt formasında qaytarır.

    `quality` parametri yalnız itkili format-lar üçün (JPEG / WEBP) istifadə olunur.
    Animasiyalı şəkillər (GIF / WEBP) hazırda yalnız ilk çərçivə kimi yazılır.
    """
    pil_fmt = to_pillow_format(target_format)
    fmt = normalize_format(target_format)
    prepared = prepare_for_format(image, fmt, background=background)

    save_kwargs: dict[str, object] = {}

    if pil_fmt == "JPEG":
        save_kwargs.update(
            {
                "quality": int(quality),
                "optimize": True,
                "progressive": True,
                "subsampling": 2,
            }
        )
    elif pil_fmt == "WEBP":
        save_kwargs.update({"quality": int(quality), "method": 6})
    elif pil_fmt == "PNG":
        save_kwargs.update({"optimize": True, "compress_level": 9})
    elif pil_fmt == "GIF":
        # Palet rejimi olmazsa, GIF üçün avtomatik çevrilir.
        if prepared.mode != "P":
            prepared = prepared.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        save_kwargs.update({"optimize": True})
    elif pil_fmt == "BMP":
        # BMP üçün xüsusi parametr yoxdur.
        pass
    elif pil_fmt == "TIFF":
        save_kwargs.update({"compression": "tiff_lzw"})
    elif pil_fmt == "ICO":
        # Çox ölçülü ikon yığımı.
        sizes = [s for s in ICO_SIZES if s[0] <= max(prepared.size)]
        if not sizes:
            sizes = [(min(prepared.size),) * 2]
        save_kwargs.update({"sizes": sizes})

    # Metadatanı saxlamaq lazım deyilsə, EXIF / ICC profilini düşürürük.
    if not keep_metadata:
        if "exif" in prepared.info:
            del prepared.info["exif"]
        if "icc_profile" in prepared.info:
            del prepared.info["icc_profile"]

    buffer = BytesIO()
    prepared.save(buffer, format=pil_fmt, **save_kwargs)
    return buffer.getvalue()


def is_animated(image: Image.Image, target_format: str) -> bool:
    """Şəkil animasiyalıdırsa və hədəf format animasiyanı dəstəkləyirsə True qaytarır."""
    n_frames = getattr(image, "n_frames", 1)
    return n_frames > 1 and normalize_format(target_format) in ANIMATION_FORMATS
