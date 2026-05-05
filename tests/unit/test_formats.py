"""`utils.formats` modulu testləri."""

from __future__ import annotations

from pathlib import Path

import pytest

from pixelforge.utils.formats import (
    extension_for,
    is_supported_input,
    normalize_format,
    supports_alpha,
    supports_animation,
    to_pillow_format,
)


@pytest.mark.parametrize(
    "given,expected",
    [
        ("jpg", "JPG"),
        ("JPEG", "JPG"),
        (".png", "PNG"),
        ("WEBP", "WEBP"),
        ("tif", "TIFF"),
        ("ico", "ICO"),
    ],
)
def test_normalize(given: str, expected: str) -> None:
    """Müxtəlif giriş variantları standart koduna uyğun gəlir."""
    assert normalize_format(given) == expected


def test_to_pillow_format() -> None:
    """Daxili kod Pillow formatına düzgün çevrilir."""
    assert to_pillow_format("JPG") == "JPEG"
    assert to_pillow_format("PNG") == "PNG"


def test_to_pillow_format_invalid() -> None:
    """Tanınmayan format `ValueError` qaldırır."""
    with pytest.raises(ValueError):
        to_pillow_format("xxx")


def test_extension_for() -> None:
    """Hər format üçün düzgün uzantı."""
    assert extension_for("JPG") == ".jpg"
    assert extension_for("PNG") == ".png"
    assert extension_for("WEBP") == ".webp"


def test_supports_alpha() -> None:
    """Alfa dəstəyi düzgün qaytarılır."""
    assert supports_alpha("PNG") is True
    assert supports_alpha("WEBP") is True
    assert supports_alpha("JPG") is False
    assert supports_alpha("BMP") is False


def test_supports_animation() -> None:
    """Animasiya dəstəyi düzgün qaytarılır."""
    assert supports_animation("GIF") is True
    assert supports_animation("WEBP") is True
    assert supports_animation("PNG") is False


def test_is_supported_input() -> None:
    """Dəstəklənən giriş uzantıları düzgün tanınır."""
    assert is_supported_input(Path("photo.jpg")) is True
    assert is_supported_input(Path("photo.HEIC")) is True
    assert is_supported_input(Path("video.mp4")) is False
    assert is_supported_input(Path("data.txt")) is False
