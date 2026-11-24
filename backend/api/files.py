from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()


@router.get("/images/{filename}")
def serve_image(filename: str):
    file_path = Path("data/images") / filename
    if not file_path.exists():
        raise HTTPException(404, detail="File not found")
    return FileResponse(file_path)


@router.get("/videos/{filename}")
def serve_video(filename: str):
    file_path = Path("data/videos") / filename
    if not file_path.exists():
        raise HTTPException(404, detail="File not found")
    return FileResponse(file_path)
