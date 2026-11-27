from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import settings
from pipeline.thumbnails import ensure_thumbnail

router = APIRouter()


def _serve(directory: Path, filename: str) -> FileResponse:
    # Only bare file names are accepted; anything else could escape the folder.
    if Path(filename).name != filename:
        raise HTTPException(400, detail="Invalid file name")
    file_path = directory / filename
    if not file_path.is_file():
        raise HTTPException(404, detail="File not found")
    return FileResponse(file_path)


@router.get("/images/{filename}")
def serve_image(filename: str):
    return _serve(settings.IMAGES_DIR, filename)


@router.get("/videos/{filename}")
def serve_video(filename: str):
    return _serve(settings.VIDEOS_DIR, filename)


@router.get("/thumbs/{artwork_id}.jpg")
def serve_thumbnail(artwork_id: str):
    if not artwork_id.isalnum():
        raise HTTPException(400, detail="Invalid id")
    sources = sorted(settings.IMAGES_DIR.glob(f"{artwork_id}.*"))
    if not sources:
        raise HTTPException(404, detail="No image for this id")
    try:
        thumb = ensure_thumbnail(artwork_id, sources[0])
    except Exception:
        # Formats Pillow cannot thumbnail: let the client fall back to the original.
        raise HTTPException(404, detail="Thumbnail not available")
    return FileResponse(thumb, headers={"Cache-Control": "public, max-age=31536000, immutable"})
