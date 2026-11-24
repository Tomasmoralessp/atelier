from pathlib import Path
import hashlib


def compute_hash(file_path: Path):
    """Compute SHA256 hash of file contents, used as unique ID."""
    hasher = hashlib.sha256()
    with open(file=file_path, mode="rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()[:16]
