"""Bayt, müddət və faiz dəyərlərini insana oxunaqlı şəkildə formatlayır."""

from __future__ import annotations


def human_bytes(n: int | float) -> str:
    """Bayt sayını qısa, oxunaqlı sətirə çevirir (məs. 1.2 MB)."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def human_duration(seconds: float) -> str:
    """Saniyəni `mm:ss` və ya `hh:mm:ss` formatına çevirir."""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def percent(part: float, whole: float) -> str:
    """İki ədədin nisbətini faiz olaraq qaytarır (məs. 'azaldı 78%')."""
    if whole <= 0:
        return "0%"
    return f"{(part / whole) * 100:.0f}%"
