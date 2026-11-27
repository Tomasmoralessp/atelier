from pathlib import Path

from PIL import Image, ImageOps

import settings

THUMB_SIZE = (480, 480)


def thumb_path(artwork_id: str) -> Path:
    return settings.THUMBS_DIR / f"{artwork_id}.jpg"


def ensure_thumbnail(artwork_id: str, source: Path) -> Path:
    """Create the grid thumbnail on first request; later requests reuse it."""
    target = thumb_path(artwork_id)
    if target.exists():
        return target
    with Image.open(source) as image:
        image.draft("RGB", THUMB_SIZE)  # fast JPEG downscale while decoding
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail(THUMB_SIZE)
        partial = target.with_suffix(".partial")
        image.save(partial, "JPEG", quality=82)
        partial.replace(target)
    return target
