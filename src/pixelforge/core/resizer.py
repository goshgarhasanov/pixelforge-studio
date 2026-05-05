"""Şəkil ölçüsünü dəyişdirmə əməliyyatları."""

from __future__ import annotations

import logging

from PIL import Image

from pixelforge.core.models import ResizeMode, ResizeOptions

logger = logging.getLogger(__name__)


def _scale_keep_aspect(size: tuple[int, int], target_w: int, target_h: int) -> tuple[int, int]:
    """En və hündürlüyü qoruyaraq verilmiş çərçivəyə uyğunlaşdırır."""
    src_w, src_h = size
    if src_w <= 0 or src_h <= 0:
        return size
    ratio = min(target_w / src_w, target_h / src_h)
    new_w = max(1, int(round(src_w * ratio)))
    new_h = max(1, int(round(src_h * ratio)))
    return new_w, new_h


def calculate_new_size(
    src_size: tuple[int, int],
    options: ResizeOptions,
) -> tuple[int, int]:
    """Verilmiş seçimlərə əsasən yeni ölçünü hesablayır.

    Heç bir əməliyyat tələb olunmursa, orijinal ölçünü qaytarır.
    """
    src_w, src_h = src_size

    if options.mode == ResizeMode.NONE:
        return src_size

    if options.mode == ResizeMode.PERCENT:
        p = (options.percent or 100.0) / 100.0
        return max(1, int(round(src_w * p))), max(1, int(round(src_h * p)))

    if options.mode == ResizeMode.LONG_EDGE:
        edge = options.edge_pixels or max(src_size)
        if src_w >= src_h:
            new_w = edge
            new_h = max(1, int(round(src_h * edge / src_w)))
        else:
            new_h = edge
            new_w = max(1, int(round(src_w * edge / src_h)))
        return new_w, new_h

    if options.mode == ResizeMode.SHORT_EDGE:
        edge = options.edge_pixels or min(src_size)
        if src_w <= src_h:
            new_w = edge
            new_h = max(1, int(round(src_h * edge / src_w)))
        else:
            new_h = edge
            new_w = max(1, int(round(src_w * edge / src_h)))
        return new_w, new_h

    # PIXELS rejimi.
    target_w = options.width or src_w
    target_h = options.height or src_h
    if options.keep_aspect:
        return _scale_keep_aspect(src_size, target_w, target_h)
    return max(1, target_w), max(1, target_h)


def resize_image(image: Image.Image, options: ResizeOptions) -> Image.Image:
    """Şəkil ölçüsünü verilmiş seçimlərə uyğun olaraq dəyişdirir.

    Ölçü artırma `allow_upscale=True` olmadan icazə verilmir.
    """
    src_size = image.size
    new_size = calculate_new_size(src_size, options)

    if new_size == src_size:
        return image

    upscaling = new_size[0] > src_size[0] or new_size[1] > src_size[1]
    if upscaling and not options.allow_upscale:
        logger.debug("Ölçü artırma icazəsi yoxdur, orijinal ölçü saxlanır.")
        return image

    return image.resize(new_size, Image.Resampling.LANCZOS)
