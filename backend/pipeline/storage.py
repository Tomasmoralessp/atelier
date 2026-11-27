import enum
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

IMAGE_EXTENSIONS = {
    ext for ext, fmt in Image.registered_extensions().items() if fmt in Image.OPEN
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


class FileType(enum.Enum):
    image = "image"
    video = "video"
    unknown = "unknown"


async def save_upload_to_temp(file: UploadFile, temp_dir: Path) -> Path:
    # Never trust the client file name for the path (it may contain folders).
    suffix = Path(file.filename or "").suffix.lower()
    destination = temp_dir / f"{uuid.uuid4().hex}{suffix}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return destination


def get_file_extension(file_path: Path) -> str:
    return file_path.suffix.lower()


def get_file_type(ext: str) -> FileType:
    if ext in IMAGE_EXTENSIONS:
        return FileType.image
    if ext in VIDEO_EXTENSIONS:
        return FileType.video
    return FileType.unknown


def is_readable_image(file_path: Path) -> bool:
    try:
        with Image.open(file_path) as image:
            image.verify()
        return True
    except Exception:
        return False


def store_file(source: Path, destination: Path, copy: bool) -> None:
    """Copy or move source into the library. Existing files are kept as-is
    (file names are content hashes, so same name means same content)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not copy:
            source.unlink(missing_ok=True)
        return
    if copy:
        shutil.copy2(source, destination)
    else:
        shutil.move(source, destination)
