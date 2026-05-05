"""`resize_image` və ölçü hesablama testləri."""

from __future__ import annotations

from PIL import Image

from pixelforge.core.models import ResizeMode, ResizeOptions
from pixelforge.core.resizer import calculate_new_size, resize_image


def test_pixels_keep_aspect() -> None:
    """Tərəflər nisbəti qorunmaqla çərçivəyə uyğunlaşdırılır."""
    new_size = calculate_new_size((4000, 3000), ResizeOptions(mode=ResizeMode.PIXELS, width=800, height=800))
    # 4:3 nisbəti — uzun tərəf 800-ə uyğunlaşmalıdır.
    assert max(new_size) == 800
    assert new_size[0] / new_size[1] == 4 / 3


def test_percent_50() -> None:
    """50% kiçildilmə tam yarı qədər ölçü verir."""
    new_size = calculate_new_size((1000, 600), ResizeOptions(mode=ResizeMode.PERCENT, percent=50))
    assert new_size == (500, 300)


def test_long_edge() -> None:
    """Uzun tərəf hədəfə bərabər olur."""
    new_size = calculate_new_size((1600, 900), ResizeOptions(mode=ResizeMode.LONG_EDGE, edge_pixels=1280))
    assert new_size[0] == 1280
    assert abs(new_size[1] - 720) <= 1


def test_no_resize_returns_same_object() -> None:
    """`NONE` rejimi orijinal şəkli olduğu kimi qaytarır."""
    img = Image.new("RGB", (100, 100))
    out = resize_image(img, ResizeOptions(mode=ResizeMode.NONE))
    assert out is img


def test_no_upscale_by_default() -> None:
    """Standart olaraq ölçü artımı baş vermir."""
    img = Image.new("RGB", (100, 100))
    out = resize_image(img, ResizeOptions(mode=ResizeMode.PIXELS, width=500, height=500))
    assert out.size == (100, 100)


def test_upscale_when_allowed() -> None:
    """Açıq icazə verildikdə ölçü arta bilər."""
    img = Image.new("RGB", (100, 100))
    out = resize_image(
        img,
        ResizeOptions(mode=ResizeMode.PIXELS, width=300, height=300, allow_upscale=True),
    )
    assert out.size == (300, 300)
