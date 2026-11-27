from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import settings

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
