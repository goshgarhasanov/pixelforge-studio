"""Tətbiqə xas (custom) xəta sinifləri.

Hər xəta UI-də uyğun bir bildiriş və göstəriş ilə müşayiət olunur.
"""

from __future__ import annotations


class PixelForgeError(Exception):
    """Bütün xəta siniflərinin əsası."""

    user_message: str = "Naməlum xəta baş verdi."
    suggestion: str = "Detalları köçürüb dəstəyə müraciət edin."

    def __init__(self, message: str = "", *, user_message: str | None = None) -> None:
        super().__init__(message or user_message or self.user_message)
        if user_message is not None:
            self.user_message = user_message


class SourceNotFoundError(PixelForgeError):
    """Mənbə fayl mövcud deyil."""

    user_message = "Mənbə fayl tapılmadı."
    suggestion = "Faylın silinmədiyini və yolunun düzgün olduğunu yoxlayın."


class UnsupportedFormatError(PixelForgeError):
    """Fayl formatı dəstəklənmir və ya tanınmır."""

    user_message = "Bu fayl formatı dəstəklənmir."
    suggestion = "Dəstəklənən formatlar: JPG, PNG, WEBP, GIF, BMP, TIFF, HEIC."


class CorruptedImageError(PixelForgeError):
    """Şəkil zədəlidir, oxuna bilmir."""

    user_message = "Şəkil zədəlidir və oxuna bilmir."
    suggestion = "Faylı başqa proqramda açıb yoxlayın və ya yenidən endirin."


class OutOfMemoryError(PixelForgeError):
    """Şəkil çox böyükdür, yaddaş çatmır."""

    user_message = "Şəkil həddən artıq böyükdür — yaddaş çatmadı."
    suggestion = "Daha kiçik ölçü hədəfi seçin və ya şəkli əvvəlcədən kiçildin."


class PermissionError_(PixelForgeError):
    """Yazma icazəsi yoxdur."""

    user_message = "Çıxış qovluğuna yazma icazəsi yoxdur."
    suggestion = "Başqa qovluq seçin və ya tətbiqi inzibatçı kimi işə salın."


class DiskFullError(PixelForgeError):
    """Diskdə yer qalmayıb."""

    user_message = "Diskdə kifayət qədər boş yer yoxdur."
    suggestion = "Lazımsız faylları silin və yenidən cəhd edin."


class CompressionTargetUnreachableError(PixelForgeError):
    """Hədəf KB-ə çatmaq mümkün olmadı (minimum tərəfdən aşağı düşür)."""

    user_message = "Verilən hədəf ölçüsünə çatmaq mümkün olmadı."
    suggestion = "Daha böyük hədəf seçin və ya format-ı WEBP-ə dəyişin."


def classify_exception(exc: BaseException) -> PixelForgeError:
    """Standart Python istisnasını tətbiqə xas xəta tipinə çevirir.

    UI tərəfində uyğun mesaj və təklif göstərmək üçün istifadə olunur.
    """
    if isinstance(exc, PixelForgeError):
        return exc

    msg = str(exc)
    name = type(exc).__name__

    if isinstance(exc, FileNotFoundError):
        return SourceNotFoundError(msg)
    if isinstance(exc, PermissionError):
        return PermissionError_(msg)
    if isinstance(exc, MemoryError):
        return OutOfMemoryError(msg)
    if isinstance(exc, OSError):
        # `errno=28` (ENOSPC) — diskdə yer yoxdur.
        if getattr(exc, "errno", None) == 28:
            return DiskFullError(msg)
        return PixelForgeError(
            msg,
            user_message=f"Sistem xətası: {msg}",
        )
    if name in ("UnidentifiedImageError", "DecompressionBombError"):
        return CorruptedImageError(msg)
    if "cannot identify image" in msg.lower() or "truncated" in msg.lower():
        return CorruptedImageError(msg)

    # Geri qalan hər şey — ümumi xəta.
    return PixelForgeError(msg, user_message=f"Gözlənilməz xəta: {msg}")
