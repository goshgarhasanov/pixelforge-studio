"""Test-lər üçün ortaq fikstürlər."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

# Paket src/ qovluğundan idxal olunur.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def sample_photo(tmp_path: Path) -> Path:
    """Sıxışdırma testlərini həqiqi şəkildə aparmaq üçün böyük JPEG yaradır."""
    img = Image.new("RGB", (2400, 1800))
    # Şəklə qradient + şüalar əlavə edirik ki, sıxışdırma triviyal olmasın.
    pixels = img.load()
    assert pixels is not None
    for y in range(img.height):
        for x in range(0, img.width, 4):
            r = (x * 255) // img.width
            g = (y * 255) // img.height
            b = ((x + y) * 255) // (img.width + img.height)
            for dx in range(4):
                if x + dx < img.width:
                    pixels[x + dx, y] = (r, g, b)
    out = tmp_path / "sample.jpg"
    img.save(out, format="JPEG", quality=95)
    return out


@pytest.fixture
def sample_png_alpha(tmp_path: Path) -> Path:
    """Şəffaflığı olan kiçik PNG yaradır."""
    img = Image.new("RGBA", (300, 200), (255, 0, 128, 180))
    out = tmp_path / "alpha.png"
    img.save(out, format="PNG")
    return out
