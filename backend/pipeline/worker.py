"""Desktop side of the queue: while the app runs in server mode, classify
artworks the server has queued (classified=False) on this machine."""

import logging
import threading

import httpx

import settings
from pipeline.orchestrator import analysis_fields, classify_safely
from pipeline.storage import is_readable_image

log = logging.getLogger("atelier.worker")

BATCH_SIZE = 8
IDLE_SECONDS = 15
ERROR_SECONDS = 60

status = {"processed": 0, "pending": None, "last_error": None}


def process_queue_once(client: httpx.Client) -> int:
    """Classify one batch from the server queue. Returns how many were done."""
    response = client.get(f"{settings.SERVER_URL}/queue", params={"limit": BATCH_SIZE})
    response.raise_for_status()
    queue = response.json()
    status["pending"] = queue["pending"]
    items = []
    for artwork in queue["items"]:
        # The 480px thumbnail is plenty (CLIP sees 224px, colors 300px) and
        # is ~30x smaller to download than the original.
        url = artwork.get("thumb_url") or artwork["file_url"]
        extension = "jpg" if artwork.get("thumb_url") else artwork["file_extension"]
        source = settings.TEMP_DIR / f"queue-{artwork['id']}.{extension}"
        with client.stream("GET", f"{settings.SERVER_URL}{url}") as download:
            download.raise_for_status()
            with source.open("wb") as f:
                for chunk in download.iter_bytes():
                    f.write(chunk)
        items.append({"id": artwork["id"], "source": source, "name": artwork["id"]})

    try:
        readable = [item for item in items if is_readable_image(item["source"])]
        failed = classify_safely(readable) if readable else []
        for item in items:
            # Unreadable files still leave the queue, just without a classification.
            ok = item in readable and item not in failed
            body = analysis_fields(item) if ok else {}
            client.put(
                f"{settings.SERVER_URL}/artworks/{item['id']}/analysis", json=body
            ).raise_for_status()
            status["processed"] += 1
    finally:
        for item in items:
            item["source"].unlink(missing_ok=True)
    return len(items)


def run_forever(stop: threading.Event) -> None:
    with httpx.Client(timeout=httpx.Timeout(30.0, read=300.0)) as client:
        while not stop.is_set():
            try:
                done = process_queue_once(client)
                status["last_error"] = None
            except Exception as e:
                log.warning("queue worker: %s", e)
                status["last_error"] = str(e)
                stop.wait(ERROR_SECONDS)
                continue
            if not done:
                stop.wait(IDLE_SECONDS)
