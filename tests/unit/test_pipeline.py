"""End-to-end pipeline testləri."""

from __future__ import annotations

from pathlib import Path

from pixelforge.core.models import Job, JobStatus
from pixelforge.core.pipeline import make_default_options, process_job


def test_full_pipeline_produces_target_file(sample_photo: Path, tmp_path: Path) -> None:
    """Tam pipeline çıxış faylını disk üzərində yaratmalıdır."""
    opts = make_default_options(output_format="JPG", target_kb=150)
    opts.output_dir = tmp_path
    job = Job(source=sample_photo, options=opts)

    result = process_job(job)

    assert result.status == JobStatus.DONE
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.output_path.stat().st_size <= int(150 * 1024 * 1.05)


def test_pipeline_handles_missing_file(tmp_path: Path) -> None:
    """Olmayan fayl üçün iş `FAILED` statusunda bitir."""
    opts = make_default_options()
    opts.output_dir = tmp_path
    job = Job(source=tmp_path / "ghost.jpg", options=opts)

    result = process_job(job)

    assert result.status == JobStatus.FAILED
    assert result.error is not None
