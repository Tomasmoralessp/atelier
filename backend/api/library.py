"""Library-level endpoints: health, folder import and backup.

Folder import and backup read and write arbitrary paths on the machine
running the backend, so they are only available in local mode.
"""

import shutil
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import settings
from database.engine import get_session
from pipeline.orchestrator import process_batch
from pipeline.storage import FileType, get_file_extension, get_file_type
from schemas.artwork import ImportSummaryResponse, SkippedFile

router = APIRouter(tags=["library"])

BACKUP_FOLDER_NAME = "Atelier Backup"


class FolderRequest(BaseModel):
    folder: str


class ScanResponse(BaseModel):
    files: list[str]
    skipped: list[SkippedFile]


class ImportPathsRequest(BaseModel):
    paths: list[str]


class BackupRequest(BaseModel):
    destination: str


class BackupResponse(BaseModel):
    backup_dir: str
    files_copied: int
    finished_at: str


def require_local_mode() -> None:
    if not settings.LOCAL_IMPORT_ENABLED:
        raise HTTPException(403, detail="Only available in local mode")


def _existing_dir(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise HTTPException(400, detail=f"Folder not found: {raw}")
    return path


@router.get("/health")
def health():
    return {
        "status": "ok",
        "mode": settings.MODE,
        "data_dir": str(settings.DATA_DIR),
        "local_import": settings.LOCAL_IMPORT_ENABLED,
    }


@router.post(
    "/import/scan", response_model=ScanResponse, dependencies=[Depends(require_local_mode)]
)
def scan_folder(request: FolderRequest):
    """List importable files in a folder (recursively), in a stable order."""
    root = _existing_dir(request.folder)
    files, skipped = [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(root).parts):
            continue  # hidden files, .DS_Store, AppleDouble "._" files
        if get_file_type(get_file_extension(path)) == FileType.unknown:
            skipped.append(SkippedFile(name=str(path.relative_to(root)), reason="not an image"))
        else:
            files.append(str(path))
    return ScanResponse(files=files, skipped=skipped)


@router.post(
    "/import/files",
    response_model=ImportSummaryResponse,
    dependencies=[Depends(require_local_mode)],
)
def import_files(request: ImportPathsRequest, session: Session = Depends(get_session)):
    """Copy the given files into the library. Originals are left untouched."""
    paths = [Path(p) for p in request.paths]
    missing = [SkippedFile(name=p.name, reason="file not found") for p in paths if not p.is_file()]
    existing = [p for p in paths if p.is_file()]
    summary = process_batch(existing, session, copy=True)
    response = ImportSummaryResponse.model_validate(summary, from_attributes=True)
    response.skipped += missing
    return response


@router.post(
    "/backup", response_model=BackupResponse, dependencies=[Depends(require_local_mode)]
)
def backup(request: BackupRequest):
    """Mirror the library into <destination>/Atelier Backup.

    The database is copied with SQLite's online backup API (safe while the
    app is running); media files are copied only if missing, since their
    names are content hashes.
    """
    destination = _existing_dir(request.destination) / BACKUP_FOLDER_NAME
    if destination.resolve() == settings.DATA_DIR.resolve():
        raise HTTPException(400, detail="Backup folder cannot be the data folder")
    destination.mkdir(exist_ok=True)

    files_copied = 0
    for media_dir in (settings.IMAGES_DIR, settings.VIDEOS_DIR):
        target_dir = destination / media_dir.name
        target_dir.mkdir(exist_ok=True)
        for source in media_dir.iterdir():
            target = target_dir / source.name
            if source.is_file() and not target.exists():
                shutil.copy2(source, target)
                files_copied += 1

    # Write to a temp name first so an interrupted backup never leaves a
    # half-written database behind.
    db_target = destination / "atelier.db"
    db_temp = destination / "atelier.db.partial"
    with closing(sqlite3.connect(settings.DB_PATH)) as src, closing(
        sqlite3.connect(db_temp)
    ) as dst:
        src.backup(dst)
    db_temp.replace(db_target)

    return BackupResponse(
        backup_dir=str(destination),
        files_copied=files_copied,
        finished_at=datetime.now().isoformat(timespec="seconds"),
    )
