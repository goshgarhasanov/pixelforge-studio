"""`compress_to_target` üçün testlər."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from pixelforge.core.compressor import compress_to_target


def _open(p: Path) -> Image.Image:
    """Test fikstürünü açır."""
    return Image.open(p)


def test_hits_200kb_target(sample_photo: Path) -> None:
    """Standart 200 KB hədəfi qarşılanmalıdır."""
    img = _open(sample_photo)
    data, report = compress_to_target(img, target_kb=200, fmt="JPEG")
    assert len(data) <= int(200 * 1024 * 1.02), f"Faktiki: {len(data)} bayt"
    assert report.target_met is True
    assert report.iterations <= 8 + 50  # quality + downscale döngüləri


def test_hits_50kb_target(sample_photo: Path) -> None:
    """Daha sıx 50 KB hədəfi də qarşılanmalıdır (downscale ilə)."""
    img = _open(sample_photo)
    data, report = compress_to_target(img, target_kb=50, fmt="JPEG")
    assert len(data) <= int(50 * 1024 * 1.05)
    assert report.final_bytes == len(data)


def test_quality_within_bounds(sample_photo: Path) -> None:
    """Son keyfiyyət həmişə [min, max] aralığında olmalıdır."""
    img = _open(sample_photo)
    _, report = compress_to_target(img, target_kb=200, fmt="JPEG", min_quality=40, max_quality=90)
    assert 40 <= report.final_quality <= 90


def test_webp_target(sample_photo: Path) -> None:
    """WEBP üçün də hədəf qarşılanmalıdır."""
    img = _open(sample_photo)
    data, report = compress_to_target(img, target_kb=150, fmt="WEBP")
    assert len(data) <= int(150 * 1024 * 1.02)
    assert report.target_met is True


def test_invalid_target_raises() -> None:
    """Mənfi hədəf rədd edilməlidir."""
    img = Image.new("RGB", (100, 100))
    with pytest.raises(ValueError):
        compress_to_target(img, target_kb=0)


def test_does_not_upscale(sample_photo: Path) -> None:
    """Şəkil heç vaxt orijinaldan böyük olmamalıdır."""
    img = _open(sample_photo)
    _, report = compress_to_target(img, target_kb=300, fmt="JPEG")
    assert report.final_width <= img.size[0]
    assert report.final_height <= img.size[1]
