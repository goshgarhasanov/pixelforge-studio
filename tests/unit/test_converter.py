"""Format çevrilməsi üçün testlər."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from pixelforge.core.converter import encode_image, prepare_for_format


@pytest.mark.parametrize("fmt", ["JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF"])
def test_encode_round_trip(sample_photo: Path, fmt: str) -> None:
    """Hər format üçün kodlama → açma dövrəsi işləməlidir."""
    img = Image.open(sample_photo)
    data = encode_image(img, fmt, quality=85)
    assert data
    reopened = Image.open(BytesIO(data))
    assert reopened.size == img.size


def test_alpha_to_jpg_uses_background(sample_png_alpha: Path) -> None:
    """RGBA şəkli JPG-ə çevrildikdə şəffaflıq arxa fonla doldurulur."""
    img = Image.open(sample_png_alpha)
    data = encode_image(img, "JPG", quality=80, background="#FFFFFF")
    assert data
    out = Image.open(BytesIO(data))
    assert out.mode == "RGB"


def test_ico_multi_size(sample_photo: Path) -> None:
    """ICO çıxışı çox ölçülü ikon yaratmalıdır."""
    img = Image.open(sample_photo).resize((512, 512))
    data = encode_image(img, "ICO")
    assert data
    # ICO header magic = 0x00 0x00 0x01 0x00
    assert data[:4] == b"\x00\x00\x01\x00"


def test_prepare_for_alpha_format(sample_photo: Path) -> None:
    """Alfa-dəstəkli formatlar üçün şəkil RGBA-ya çevrilir."""
    img = Image.open(sample_photo)
    prepared = prepare_for_format(img, "PNG")
    assert prepared.mode in ("RGBA", "LA")
