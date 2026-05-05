"""Sadə tərcümə sistemi.

UI strinqləri Azərbaycan dilində standart-dır; digər dillər `i18n/<kod>.json`
faylından yüklənir. Açar tapılmazsa, açarın özü qaytarılır.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pixelforge.utils.paths import project_root

logger = logging.getLogger(__name__)

# Standart Azərbaycan dilində strinqlər (kod içində qalır — fayl yüklənmə xərci olmasın).
DEFAULT_STRINGS_AZ: dict[str, str] = {
    # --- Tətbiq adı və başlıqlar ---
    "app.title": "PixelForge Studio",
    "app.tagline": "Hər pikseli ustalıqla emal et",
    # --- Səhifələr / yan menyu ---
    "nav.home": "Əsas",
    "nav.convert": "Çevir",
    "nav.resize": "Ölçü dəyişdir",
    "nav.compress": "Sıxışdır",
    "nav.recipes": "Reseptlər",
    "nav.stats": "Statistika",
    "nav.logs": "Qeydlər",
    "nav.settings": "Tənzimləmələr",
    # --- Düymələr ---
    "btn.start": "Başla",
    "btn.cancel": "Ləğv et",
    "btn.pause": "Dayandır",
    "btn.resume": "Davam et",
    "btn.clear": "Təmizlə",
    "btn.browse": "Fayl seç",
    "btn.add_files": "Fayl əlavə et",
    "btn.add_folder": "Qovluq əlavə et",
    "btn.open_output": "Çıxış qovluğunu aç",
    "btn.remove": "Sil",
    "btn.forge": "İndi emal et",
    # --- Drop zone ---
    "drop.title": "Şəkilləri buraya sürüklə və burax",
    "drop.subtitle": "və ya seçmək üçün klikləyin",
    "drop.formats": "Dəstəklənən: JPG · PNG · WEBP · GIF · BMP · TIFF · HEIC",
    # --- Növbə ---
    "queue.title": "Növbə",
    "queue.empty": "Növbə boşdur — başlamaq üçün şəkillər əlavə edin",
    "queue.col.file": "Fayl",
    "queue.col.size": "Ölçü",
    "queue.col.target": "Nəticə",
    "queue.col.status": "Vəziyyət",
    # --- Status etiketləri ---
    "status.queued": "Növbədə",
    "status.running": "Emal olunur",
    "status.done": "Tamamlandı",
    "status.failed": "Xəta",
    "status.cancelled": "Ləğv edildi",
    "status.ready": "Hazırdır",
    # --- Tənzimləmələr paneli ---
    "settings.format": "Çıxış formatı",
    "settings.resize_mode": "Ölçü rejimi",
    "settings.width": "En",
    "settings.height": "Hündürlük",
    "settings.percent": "Faiz",
    "settings.target_kb": "Hədəf ölçü (KB)",
    "settings.quality": "Keyfiyyət",
    "settings.output_dir": "Çıxış qovluğu",
    "settings.keep_aspect": "Tərəflər nisbətini qoru",
    "settings.background": "Arxa fon rəngi",
    "settings.theme": "Mövzu",
    "settings.language": "Dil",
    "settings.parallel": "Paralel işçilər",
    # --- Ölçü rejimləri ---
    "resize.none": "Dəyişmə",
    "resize.pixels": "Piksel (en × hündürlük)",
    "resize.percent": "Faiz",
    "resize.long_edge": "Uzun tərəf",
    "resize.short_edge": "Qısa tərəf",
    # --- Bildirişlər ---
    "toast.batch_started": "Toplu emal başladı",
    "toast.batch_done": "Bütün şəkillər emal edildi",
    "toast.batch_cancelled": "Emal ləğv edildi",
    "toast.no_files": "Heç bir fayl seçilməyib",
    "toast.invalid_files": "Bu fayllar dəstəklənmir: {names}",
    # --- Status bar ---
    "statusbar.files": "{n} fayl",
    "statusbar.saved": "Qənaət: {size}",
    "statusbar.eta": "Qalan vaxt: {time}",
    # --- Loglar ---
    "logs.title": "Tətbiq qeydləri",
    "logs.clear": "Qeydləri təmizlə",
    # --- Xəta dialoqları ---
    "error.title": "Xəta baş verdi",
    "error.copy": "Detalları köçür",
    "error.dismiss": "Bağla",
}


_current_lang = "az"
_translations: dict[str, dict[str, str]] = {"az": DEFAULT_STRINGS_AZ}


def set_language(lang: str) -> None:
    """Cari dili dəyişir və lazımdırsa fayldan tərcümələri yükləyir."""
    global _current_lang
    lang = (lang or "az").lower()
    if lang not in _translations:
        path: Path = project_root() / "i18n" / f"{lang}.json"
        if path.exists():
            try:
                _translations[lang] = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Tərcümə faylı yüklənmədi (%s): %s", lang, exc)
                _translations[lang] = {}
        else:
            _translations[lang] = {}
    _current_lang = lang


def t(key: str, **kwargs: object) -> str:
    """Açar üçün tərcüməni qaytarır; tapılmazsa, az versiyasına yıxılır."""
    table = _translations.get(_current_lang, DEFAULT_STRINGS_AZ)
    s = table.get(key) or DEFAULT_STRINGS_AZ.get(key) or key
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s
