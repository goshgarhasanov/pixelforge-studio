"""PixelForge Studio loqosunu generasiya edir (PNG + ICO).

Pillow ilə vektor benzeri stil — gradient piksel-anvil mark + Inter wordmark.
İcra: `python scripts/build_logo.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "logo"

# Brend rəngləri (PROMPT.md-dən).
GRADIENT_STOPS = [
    (0.00, (99, 102, 241)),    # Indigo  #6366F1
    (0.50, (217, 70, 239)),    # Fuchsia #D946EF
    (1.00, (245, 158, 11)),    # Amber   #F59E0B
]


def _gradient_color(t: float) -> tuple[int, int, int]:
    """[0..1] aralığında qradient rəngini interpolyasiya edir."""
    if t <= GRADIENT_STOPS[0][0]:
        return GRADIENT_STOPS[0][1]
    if t >= GRADIENT_STOPS[-1][0]:
        return GRADIENT_STOPS[-1][1]
    for i in range(len(GRADIENT_STOPS) - 1):
        a_t, a_c = GRADIENT_STOPS[i]
        b_t, b_c = GRADIENT_STOPS[i + 1]
        if a_t <= t <= b_t:
            ratio = (t - a_t) / (b_t - a_t)
            return tuple(int(a_c[k] + (b_c[k] - a_c[k]) * ratio) for k in range(3))  # type: ignore[return-value]
    return GRADIENT_STOPS[-1][1]


def _draw_gradient_square(
    draw: ImageDraw.ImageDraw, x: int, y: int, size: int, t: float
) -> None:
    """Verilmiş yerə qradient-rəngli yumru künclü kvadrat çəkir."""
    color = _gradient_color(t)
    radius = max(2, size // 6)
    draw.rounded_rectangle(
        [x, y, x + size, y + size],
        radius=radius,
        fill=color,
    )


def make_mark(size: int = 512) -> Image.Image:
    """Loqonun yalnız mark hissəsini (piksel-anvil stilizasiyası) çəkir."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 5×5 piksel şəbəkəsi üzərində anvil silueti.
    # 1 = doldurulur, 0 = boş. Aşağıdakı şablon stilizə edilmiş zindandır:
    #   _ X X X _
    #   X X X X X
    #   _ X X X _
    #   _ _ X _ _
    #   _ X X X _
    pattern = [
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
    ]
    grid = 5
    pad = size // 12
    cell = (size - 2 * pad) // grid
    actual = cell * grid
    offset = (size - actual) // 2

    for r, row in enumerate(pattern):
        for c, on in enumerate(row):
            if not on:
                continue
            # Qradient mövqeyi: yuxarıdan aşağıya, soldan sağa diaqonal.
            t = (r + c) / (2 * (grid - 1))
            x = offset + c * cell
            y = offset + r * cell
            _draw_gradient_square(draw, x, y, cell - max(2, cell // 12), t)

    # Yuxarıdakı qığılcım — kiçik amber dairəcik.
    spark_size = max(6, cell // 4)
    spark_x = offset + 2 * cell + (cell - spark_size) // 2
    spark_y = offset - spark_size - max(2, cell // 8)
    if spark_y > 0:
        draw.ellipse(
            [spark_x, spark_y, spark_x + spark_size, spark_y + spark_size],
            fill=GRADIENT_STOPS[-1][1],
        )

    return img


def make_full_logo(width: int = 1024, height: int = 320) -> Image.Image:
    """Mark + wordmark birgə (üfüqi) loqosunu çəkir."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mark_size = int(height * 0.85)
    mark = make_mark(mark_size)
    margin = (height - mark_size) // 2
    img.paste(mark, (margin, margin), mark)

    draw = ImageDraw.Draw(img)
    text_x = margin + mark_size + margin
    # Şrift yüklənməsi (Windows-da Inter / Segoe UI).
    try:
        font_main = ImageFont.truetype("seguisb.ttf", int(height * 0.42))
        font_sub = ImageFont.truetype("segoeui.ttf", int(height * 0.20))
    except OSError:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    main_color = (240, 240, 248, 255)
    sub_color = (168, 168, 192, 255)
    draw.text((text_x, int(height * 0.12)), "PixelForge", fill=main_color, font=font_main)
    draw.text((text_x, int(height * 0.62)), "STUDIO", fill=sub_color, font=font_sub)
    return img


def main() -> int:
    """Bütün loqo variantlarını generasiya edir və diskə yazır."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Mark — kvadrat.
    mark = make_mark(1024)
    mark.save(OUT_DIR / "logo-mark.png")
    mark.save(OUT_DIR / "icon.png")

    # 2) Tam loqo (mark + wordmark, üfüqi).
    full = make_full_logo(1280, 360)
    full.save(OUT_DIR / "logo-full.png")

    # 3) Çoxölçülü ICO.
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for w, _h in sizes:
        thumb = make_mark(max(w, 64))  # kiçik ölçülərdə daha aydın
        thumb = thumb.resize((w, w), Image.Resampling.LANCZOS)
        icons.append(thumb)
    icons[-1].save(OUT_DIR / "icon.ico", format="ICO", sizes=sizes)

    print(f"Logo files generated at: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
