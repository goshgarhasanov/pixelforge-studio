"""Şəkil format-larının validasiyası və köməkçi funksiyalar."""

from __future__ import annotations

from pathlib import Path

# Daxili format kodları → Pillow formatına uyğunluq cədvəli.
PILLOW_FORMAT: dict[str, str] = {
    "JPG": "JPEG",
    "JPEG": "JPEG",
    "PNG": "PNG",
    "WEBP": "WEBP",
    "GIF": "GIF",
    "BMP": "BMP",
    "TIFF": "TIFF",
    "ICO": "ICO",
}

# Standart fayl uzantıları.
EXTENSIONS: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
    "BMP": ".bmp",
    "TIFF": ".tiff",
    "ICO": ".ico",
}

# Dəstəklənən giriş uzantıları (oxumaq üçün).
SUPPORTED_INPUT_EXTS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".ico", ".heic", ".heif"}
)

# Dəstəklənən çıxış format-ları (yazmaq üçün).
SUPPORTED_OUTPUT_FORMATS: tuple[str, ...] = ("JPG", "PNG", "WEBP", "GIF", "BMP", "TIFF", "ICO")

# Şəffaflığı (alfa kanalı) dəstəkləyən format-lar.
ALPHA_FORMATS: frozenset[str] = frozenset({"PNG", "WEBP", "GIF", "TIFF", "ICO"})

# Animasiyanı dəstəkləyən format-lar.
ANIMATION_FORMATS: frozenset[str] = frozenset({"GIF", "WEBP"})


def normalize_format(fmt: str) -> str:
    """İstifadəçi verdiyi format kodunu standart formaya gətirir (məs. 'jpg' → 'JPG')."""
    f = fmt.strip().upper().lstrip(".")
    if f == "JPEG":
        return "JPG"
    if f == "TIF":
        return "TIFF"
    return f


def to_pillow_format(fmt: str) -> str:
    """Daxili format kodunu Pillow-un gözlədiyi formata çevirir."""
    key = normalize_format(fmt)
    if key not in PILLOW_FORMAT:
        raise ValueError(f"Dəstəklənməyən format: {fmt}")
    return PILLOW_FORMAT[key]


def extension_for(fmt: str) -> str:
    """Format üçün standart fayl uzantısını qaytarır (nöqtə daxil olmaqla)."""
    return EXTENSIONS[to_pillow_format(fmt)]


def is_supported_input(path: Path) -> bool:
    """Verilmiş yolun dəstəklənən giriş şəkli olub-olmadığını yoxlayır."""
    return path.suffix.lower() in SUPPORTED_INPUT_EXTS


def supports_alpha(fmt: str) -> bool:
    """Format şəffaflığı dəstəkləyirsə True qaytarır."""
    return normalize_format(fmt) in ALPHA_FORMATS


def supports_animation(fmt: str) -> bool:
    """Format animasiyanı dəstəkləyirsə True qaytarır."""
    return normalize_format(fmt) in ANIMATION_FORMATS
