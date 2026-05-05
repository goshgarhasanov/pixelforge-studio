"""Xəta təsnifatı testləri."""

from __future__ import annotations

import errno

from pixelforge.core.exceptions import (
    CorruptedImageError,
    DiskFullError,
    OutOfMemoryError,
    PermissionError_,
    PixelForgeError,
    SourceNotFoundError,
    classify_exception,
)


def test_classify_file_not_found() -> None:
    """`FileNotFoundError` → `SourceNotFoundError`."""
    result = classify_exception(FileNotFoundError("yoxdur"))
    assert isinstance(result, SourceNotFoundError)
    assert "tapılmadı" in result.user_message.lower()


def test_classify_permission_error() -> None:
    """`PermissionError` → `PermissionError_`."""
    result = classify_exception(PermissionError("rədd"))
    assert isinstance(result, PermissionError_)


def test_classify_memory_error() -> None:
    """`MemoryError` → `OutOfMemoryError`."""
    result = classify_exception(MemoryError())
    assert isinstance(result, OutOfMemoryError)


def test_classify_disk_full() -> None:
    """`OSError` ENOSPC → `DiskFullError`."""
    err = OSError(errno.ENOSPC, "no space")
    result = classify_exception(err)
    assert isinstance(result, DiskFullError)


def test_classify_corrupted_via_message() -> None:
    """Mesajdakı 'cannot identify image' → `CorruptedImageError`."""
    result = classify_exception(Exception("cannot identify image"))
    assert isinstance(result, CorruptedImageError)


def test_pixelforge_error_passthrough() -> None:
    """Mövcud `PixelForgeError` olduğu kimi qaytarılır."""
    original = SourceNotFoundError("test")
    result = classify_exception(original)
    assert result is original


def test_unknown_exception_wrapped() -> None:
    """Tanınmayan istisna ümumi `PixelForgeError` ilə bürünür."""
    result = classify_exception(ValueError("test"))
    assert isinstance(result, PixelForgeError)
    assert result.user_message
