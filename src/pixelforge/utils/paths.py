"""Layihə yollarını və qovluqlarını idarə edir."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Layihənin kök qovluğunu qaytarır.

    PyInstaller ilə paketlənmiş halda `sys.executable` qovluğu qaytarılır,
    inkişaf rejimində isə paketin iki səviyyə yuxarısı.
    """
    if getattr(sys, "frozen", False):  # PyInstaller bundle
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def output_dir() -> Path:
    """Standart çıxış qovluğunu qaytarır və mövcud deyilsə yaradır."""
    path = project_root() / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    """Log qovluğunu qaytarır və mövcud deyilsə yaradır."""
    path = project_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def assets_dir() -> Path:
    """Statik resursların (logo, ikonlar) qovluğunu qaytarır."""
    return project_root() / "assets"
