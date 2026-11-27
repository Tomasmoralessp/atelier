from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import settings
import database.engine  # noqa: F401  creates the data folder and tables

from api.artworks import router as artwork_router
from api.files import router as files_router
from api.library import router as library_router
from api.tags import router as tags_router

app = FastAPI(title="Atelier")

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
