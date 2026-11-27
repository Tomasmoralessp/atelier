import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import settings
import database.engine  # noqa: F401  creates the data folder and tables

from api.artworks import router as artwork_router
from api.files import router as files_router
from api.library import router as library_router
from api.queue import router as queue_router
from api.tags import router as tags_router


def background_job():
    """Server: import the inbox folder. Desktop in server mode: work the queue."""
    if settings.MODE == "remote":
        from pipeline import inbox

        return inbox.run_forever
    if settings.SERVER_URL:
        from pipeline import worker

        return worker.run_forever
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    job = background_job()
    stop = threading.Event()
    if job:
        threading.Thread(target=job, args=(stop,), daemon=True).start()
    yield
    stop.set()


app = FastAPI(title="Atelier", lifespan=lifespan)

# In local mode the API listens on the user's machine and can read local
# folders, so only the desktop app (and the Vite dev server) may call it.
# A remote server sits behind its own reverse proxy and stays open.
LOCAL_ORIGINS = [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_ORIGINS if settings.MODE == "local" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(artwork_router)
app.include_router(tags_router)
app.include_router(files_router)
app.include_router(library_router)
app.include_router(queue_router)


@app.get("/worker")
def worker_status():
    """Desktop in server mode: progress of the local queue worker."""
    from pipeline import worker

    return {"enabled": bool(settings.SERVER_URL), **worker.status}
