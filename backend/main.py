from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

import database.engine

from api.artworks import router as artwork_router
from api.tags import router as tags_router
from api.files import router as files_router

app = FastAPI(title="Atelier")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(artwork_router)
app.include_router(tags_router)
app.include_router(files_router)
