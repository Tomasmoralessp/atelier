"""Server side: files dropped into DATA_DIR/inbox (e.g. over SMB) are moved
into the library and wait in the queue for a desktop app to classify them.
Files that cannot be imported (duplicates, non-images) go to inbox/_skipped.
"""

import logging
import shutil
import threading
import time
from pathlib import Path

import settings
from database.engine import Session
from pipeline.orchestrator import process_batch
from pipeline.thumbnails import ensure_thumbnail

log = logging.getLogger("atelier.inbox")

SCAN_INTERVAL_SECONDS = 30
BATCH_SIZE = 200
SETTLE_SECONDS = 30  # skip files still being copied in
SKIPPED_DIR = "_skipped"


def _ready_files(inbox: Path) -> list[Path]:
    now = time.time()
    files = []
    for path in sorted(inbox.rglob("*")):
        relative = path.relative_to(inbox).parts
        if relative[0] == SKIPPED_DIR or any(part.startswith(".") for part in relative):
            continue
        if path.is_file() and now - path.stat().st_mtime > SETTLE_SECONDS:
            files.append(path)
            if len(files) >= BATCH_SIZE:
                break
    return files


def _remove_empty_dirs(inbox: Path) -> None:
    for directory in sorted(inbox.rglob("*"), reverse=True):
        if directory.is_dir() and directory.name != SKIPPED_DIR and not any(directory.iterdir()):
            directory.rmdir()


def process_inbox_once(inbox: Path | None = None) -> int:
    """Import one batch from the inbox. Returns how many files were handled."""
    inbox = inbox or settings.INBOX_DIR
    files = _ready_files(inbox)
    if not files:
        return 0
    names = [str(f.relative_to(inbox)) for f in files]
    with Session() as session:
        summary = process_batch(files, session, copy=False, names=names)

    for path, name in zip(files, names):
        if path.exists():  # not moved into the library: duplicate or unsupported
            target = inbox / SKIPPED_DIR / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, target)
    _remove_empty_dirs(inbox)

    # Pre-build thumbnails so the gallery is fast on first view.
    for image in settings.IMAGES_DIR.iterdir():
        try:
            ensure_thumbnail(image.stem, image)
        except Exception:
            pass
    log.info(
        "inbox: %d imported, %d duplicates, %d skipped",
        len(summary.imported), len(summary.duplicates), len(summary.skipped),
    )
    return len(files)


def run_forever(stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            handled = process_inbox_once()
        except Exception:
            log.exception("inbox scan failed")
            handled = 0
        if not handled:
            stop.wait(SCAN_INTERVAL_SECONDS)
