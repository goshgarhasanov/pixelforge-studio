"""İstifadəçi tənzimləmələrinin yüklənməsi və saxlanması."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".pixelforge"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass(slots=True)
class AppConfig:
    """İstifadəçi səviyyəli tətbiq tənzimləmələri."""

    theme: str = "dark"                  # "dark" | "light" | "system"
    accent: str = "blue"                 # CustomTkinter üçün rəng teması
    language: str = "az"                 # "az" | "tr" | "en"
    output_dir: str | None = None        # Standart çıxış qovluğu (None → layihə qovluğu)
    target_kb: int = 200                 # Sıxışdırma hədəfi
    last_format: str = "JPG"             # Son seçilmiş çıxış format-ı
    parallel_workers: int = 2            # Paralel iş sayı
    confetti: bool = True                # Tamamlanma effektləri
    auto_open_output: bool = False       # Bitdikdə qovluğu aç
    keep_recent: list[str] = field(default_factory=list)  # Son istifadə olunan fayllar


def load_config() -> AppConfig:
    """Konfiqurasiyanı diskdən yükləyir, mövcud deyilsə standart dəyərlərlə qaytarır."""
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return AppConfig(**data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Konfiqurasiya yüklənə bilmədi, standart istifadə olunur: %s", exc)
    return AppConfig()


def save_config(cfg: AppConfig) -> None:
    """Konfiqurasiyanı diskə yazır (atomik şəkildə)."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.error("Konfiqurasiya saxlanmadı: %s", exc)
