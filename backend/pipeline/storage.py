import enum
import shutil
from fastapi import UploadFile
from PIL import Image
from pathlib import Path
import mimetypes


IMAGE_EXTENSIONS = set(Image.registered_extensions().keys())
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


class FileType(enum.Enum):
    image = "image"
    video = "video"
    unknown = "unknown"


async def save_upload_to_temp(file: UploadFile, temp_dir: Path) -> Path:
    destination = temp_dir / file.filename
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    destination.write_bytes(contents)
    return destination


def get_file_extension(file_path: Path) -> str:
    return file_path.suffix.lower()


def get_file_type(ext: str) -> FileType:
    if ext in IMAGE_EXTENSIONS:
        return FileType.image
    elif ext in VIDEO_EXTENSIONS:
        return FileType.video
    return FileType.unknown


def move_to_storage(
    file_id: str,
    file_extension: str,
    file_path: Path,
    file_type: FileType,
    image_dir: Path,
    video_dir: Path,
    unknown_dir: Path,
) -> str:
    if file_type == FileType.image:
        storage_dir = image_dir
    elif file_type == FileType.video:
        storage_dir = video_dir
    else:
        storage_dir = unknown_dir

    destination = Path(storage_dir) / f"{file_id}{file_extension}"

    Path(storage_dir).mkdir(parents=True, exist_ok=True)

    if destination.exists():
        return str(destination)

    shutil.move(file_path, destination)
    return str(destination)
