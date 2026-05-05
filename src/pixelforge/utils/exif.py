"""EXIF metadatasını oxumaq və şəkli düzgün istiqamətə çevirmək üçün köməkçilər."""

from __future__ import annotations

from PIL import Image, ImageOps


def auto_orient(image: Image.Image) -> Image.Image:
    """EXIF orientation tag-ına görə şəkli düzgün istiqamətə çevirir.

    Şəkli kameranın çevrilmiş halını nəzərə alaraq düzəldir, EXIF
    metadatasını isə təmizləyir (sonradan yenidən təyin olunmaq üçün).
    """
    try:
        return ImageOps.exif_transpose(image)
    except Exception:
        # EXIF zədəlidirsə, orijinal şəkli qaytar.
        return image
