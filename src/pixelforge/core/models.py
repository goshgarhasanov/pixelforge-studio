"""Tətbiqdə istifadə olunan əsas məlumat modelləri (dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class JobStatus(str, Enum):
    """Toplu növbədəki bir işin vəziyyəti."""

    QUEUED = "queued"        # Növbədə gözləyir
    RUNNING = "running"      # İcra olunur
    DONE = "done"            # Uğurla tamamlandı
    FAILED = "failed"        # Xəta ilə bitdi
    CANCELLED = "cancelled"  # İstifadəçi tərəfindən ləğv edildi


class ResizeMode(str, Enum):
    """Ölçü dəyişdirmə üsulları."""

    NONE = "none"              # Ölçü dəyişdirilmir
    PIXELS = "pixels"          # Dəqiq ölçü (en × hündürlük)
    PERCENT = "percent"        # Faizlə miqyaslama
    LONG_EDGE = "long_edge"    # Uzun tərəf piksel ilə
    SHORT_EDGE = "short_edge"  # Qısa tərəf piksel ilə


@dataclass(slots=True)
class ResizeOptions:
    """Ölçü dəyişdirmə üçün parametrlər."""

    mode: ResizeMode = ResizeMode.NONE
    width: int | None = None
    height: int | None = None
    percent: float | None = None
    edge_pixels: int | None = None
    keep_aspect: bool = True
    allow_upscale: bool = False


@dataclass(slots=True)
class CompressionOptions:
    """Sıxışdırma üçün parametrlər."""

    enabled: bool = True
    target_kb: int = 200      # Hədəf fayl ölçüsü (kilobayt)
    min_quality: int = 35
    max_quality: int = 95
    min_short_edge: int = 320  # Aşağı piksel həddi (kiçilməyə dəyməz)


@dataclass(slots=True)
class ConvertOptions:
    """Format çevrilməsi üçün parametrlər."""

    output_format: str = "JPG"            # Hədəf format kodu
    background: str = "#FFFFFF"           # Şəffaflığı doldurmaq üçün rəng
    keep_metadata: bool = False           # EXIF saxlanılsın?
    strip_gps: bool = True                # GPS məlumatı silinsin?


@dataclass(slots=True)
class JobOptions:
    """Bir şəkil üçün tam emal parametrlər toplusu."""

    convert: ConvertOptions = field(default_factory=ConvertOptions)
    resize: ResizeOptions = field(default_factory=ResizeOptions)
    compress: CompressionOptions = field(default_factory=CompressionOptions)
    output_dir: Path | None = None        # None olarsa, standart `output/` istifadə olunur


@dataclass(slots=True)
class Job:
    """Növbədəki bir şəkil işi."""

    source: Path
    options: JobOptions
    status: JobStatus = JobStatus.QUEUED
    output_path: Path | None = None
    original_size: int = 0           # Bayt
    final_size: int = 0              # Bayt
    duration_ms: int = 0
    error: str | None = None         # İstifadəçi mesajı
    error_suggestion: str | None = None
    error_traceback: str | None = None

    @property
    def saved_bytes(self) -> int:
        """Sıxışdırma nəticəsində qənaət edilən bayt miqdarı."""
        if self.final_size and self.original_size:
            return max(0, self.original_size - self.final_size)
        return 0


@dataclass(slots=True)
class CompressionReport:
    """`compress_to_target` funksiyasının nəticə hesabatı."""

    final_quality: int
    final_width: int
    final_height: int
    final_bytes: int
    iterations: int
    downscaled: bool
    target_met: bool
