import math

from .constants import MAX_RENDER_PIXELS


def format_bytes(size):
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


def calculate_grid_columns(width, card_width=176):
    return max(1, int(max(width, card_width) // card_width))


def calculate_fit_scale(image_size, viewport_size, allow_upscale=False):
    image_width, image_height = image_size
    viewport_width, viewport_height = viewport_size
    if min(image_width, image_height, viewport_width, viewport_height) <= 0:
        return 1.0

    scale = min(viewport_width / image_width, viewport_height / image_height)
    return scale if allow_upscale else min(scale, 1.0)


def calculate_safe_zoom_limit(image_size, max_pixels=MAX_RENDER_PIXELS):
    width, height = image_size
    if width <= 0 or height <= 0:
        return 4.0
    return max(0.05, min(4.0, math.sqrt(max_pixels / (width * height))))
