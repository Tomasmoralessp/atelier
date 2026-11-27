"""Desktop app classifies locally and stores on a remote server (the NAS)."""

import json
import socket
import subprocess
import sys
import time

import httpx
import pytest

from conftest import BACKEND_DIR


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(tmp_path):
    """A real backend in remote mode, in its own process and data folder."""
    port = _free_port()
    data_dir = tmp_path / "nas"
    process = subprocess.Popen(
        [sys.executable, "run.py", "--port", str(port), "--data-dir", str(data_dir)],
        cwd=BACKEND_DIR,
        env={"ATELIER_MODE": "remote", "PATH": ""},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(120):
            try:
                if httpx.get(f"{url}/health").status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.25)
        else:
            raise RuntimeError("server did not start")
        yield url, data_dir
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_import_is_classified_locally_and_stored_on_server(
    start_app, monkeypatch, server, mixed_folder, tmp_path
):
    url, nas_dir = server
    monkeypatch.setenv("ATELIER_SERVER_URL", url)
    local = start_app(tmp_path / "local")

    files = local.post("/import/scan", json={"folder": str(mixed_folder)}).json()["files"]
    summary = local.post("/import/files", json={"paths": files}).json()

    assert sorted(summary["imported"]) == ["blue.png", "red.jpg"]
    assert summary["duplicates"] == ["blue-copy.png"]

    artworks = httpx.get(f"{url}/artworks/").json()
    assert {a["image_type"] for a in artworks} == {"painting"}  # from the local classifier
    assert all(len(a["colors"]) == 1 for a in artworks)
    assert all((nas_dir / a["file_path"]).is_file() for a in artworks)
    assert local.get("/artworks/").json() == []  # nothing stored locally

    again = local.post("/import/files", json={"paths": files}).json()
    assert again["imported"] == [] and len(again["duplicates"]) == 3


def test_ingest_rejects_mismatched_content(start_app, monkeypatch):
    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app()
    metadata = {"id": "0" * 16, "file_type": "image", "file_extension": "png"}
    response = client.post(
        "/artworks/ingest",
        data={"metadata": json.dumps(metadata)},
        files={"file": ("x.png", b"not the right bytes")},
    )
    assert response.status_code == 400
    assert client.get("/artworks/").json() == []


def test_server_without_clip_stores_uploads_with_colors_only(
    start_app, monkeypatch, mixed_folder
):
    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app(fake_model=False)
    import pipeline.orchestrator

    monkeypatch.setattr(pipeline.orchestrator, "CLIP_AVAILABLE", False)
    png = (mixed_folder / "blue.png").read_bytes()
    summary = client.post("/artworks", files=[("files", ("blue.png", png, "image/png"))]).json()

    assert summary["imported"] == ["blue.png"]
    [artwork] = client.get("/artworks/").json()
    assert artwork["image_type"] is None
    assert artwork["colors"]
