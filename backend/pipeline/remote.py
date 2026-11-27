"""Client for pushing classified artworks to a remote Atelier server."""

import json
from pathlib import Path

import httpx

import settings

TIMEOUT = httpx.Timeout(30.0, read=120.0)


def _url(path: str) -> str:
    return f"{settings.SERVER_URL}{path}"


def existing_ids(ids: list[str]) -> set[str]:
    if not ids:
        return set()
    response = httpx.post(_url("/artworks/known"), json={"ids": ids}, timeout=TIMEOUT)
    response.raise_for_status()
    return set(response.json()["known"])


def push(metadata: dict, source: Path, name: str) -> str:
    """Upload one file with its analysis. Returns 'imported' or 'duplicate'."""
    with source.open("rb") as f:
        response = httpx.post(
            _url("/artworks/ingest"),
            data={"metadata": json.dumps(metadata)},
            files={"file": (name, f)},
            timeout=TIMEOUT,
        )
    response.raise_for_status()
    return response.json()["status"]
