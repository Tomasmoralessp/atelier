"""Runtime settings, resolved once from environment variables.

ATELIER_MODE      local (default) | remote
ATELIER_DATA_DIR  folder holding atelier.db, images/, videos/ ...
ATELIER_MODEL_PATH optional path to bundled CLIP weights (offline use)
ATELIER_SERVER_URL local mode only: classify here, store on this server (NAS)
"""

import os
import sys
from pathlib import Path


def default_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Atelier"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", home)) / "Atelier"
    return Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share")) / "atelier"


MODE = os.environ.get("ATELIER_MODE", "local").lower()
if MODE not in ("local", "remote"):
    raise ValueError(f"ATELIER_MODE must be 'local' or 'remote', got {MODE!r}")

DATA_DIR = Path(os.environ.get("ATELIER_DATA_DIR") or default_data_dir()).expanduser()
DB_PATH = DATA_DIR / "atelier.db"
IMAGES_DIR = DATA_DIR / "images"
VIDEOS_DIR = DATA_DIR / "videos"
TEMP_DIR = DATA_DIR / "temp"
MODELS_DIR = DATA_DIR / "models"

MODEL_PATH = os.environ.get("ATELIER_MODEL_PATH") or None

SERVER_URL = (os.environ.get("ATELIER_SERVER_URL") or "").rstrip("/") or None

# Importing straight from a folder on disk only makes sense when the backend
# runs on the user's own machine.
LOCAL_IMPORT_ENABLED = MODE == "local"


def ensure_data_dirs() -> None:
    for directory in (DATA_DIR, IMAGES_DIR, VIDEOS_DIR, TEMP_DIR, MODELS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def resolve_media_path(stored_path: str) -> Path:
    """Stored paths are relative to DATA_DIR.

    Legacy rows hold absolute paths (e.g. /app/data/images/x.png from Docker);
    those are re-anchored on DATA_DIR when they no longer exist.
    """
    path = Path(stored_path)
    if not path.is_absolute():
        return DATA_DIR / path
    if path.exists():
        return path
    return DATA_DIR / path.parent.name / path.name
