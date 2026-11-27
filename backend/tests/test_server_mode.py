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


def test_uploads_to_server_wait_in_queue(start_app, monkeypatch, mixed_folder):
    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app()
    png = (mixed_folder / "blue.png").read_bytes()
    summary = client.post("/artworks", files=[("files", ("blue.png", png, "image/png"))]).json()

    assert summary["imported"] == ["blue.png"]
    [artwork] = client.get("/artworks/").json()
    assert artwork["classified"] is False and artwork["image_type"] is None
    queue = client.get("/queue").json()
    assert queue["pending"] == 1 and queue["items"][0]["id"] == artwork["id"]


def test_analysis_leaves_queue_and_keeps_reviewed_fields(start_app, monkeypatch, mixed_folder):
    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app()
    for name in ("blue.png", "series/red.jpg"):
        data = (mixed_folder / name).read_bytes()
        client.post("/artworks", files=[("files", (name, data, "image/png"))])
    first, second = client.get("/artworks/").json()
    client.patch(f"/artworks/{second['id']}", params={"image_type": "drawing", "reviewed": True})

    analysis = {
        "image_type": "painting",
        "colors": [{"rgb": [1, 2, 3], "lab": [1.0, 0.0, 0.0], "percentage": 100.0}],
    }
    for artwork in (first, second):
        assert client.put(f"/artworks/{artwork['id']}/analysis", json=analysis).status_code == 200

    by_id = {a["id"]: a for a in client.get("/artworks/").json()}
    assert by_id[first["id"]]["image_type"] == "painting"
    assert by_id[second["id"]]["image_type"] == "drawing"  # person's choice wins
    assert all(a["classified"] and a["colors"] for a in by_id.values())
    assert client.get("/queue").json()["pending"] == 0


def test_inbox_moves_files_into_queue(start_app, monkeypatch, mixed_folder, tmp_path):
    import os
    import shutil

    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app()
    inbox = tmp_path / "library" / "inbox"
    shutil.copytree(mixed_folder, inbox / "ari")
    for path in inbox.rglob("*"):
        os.utime(path, (0, 0))  # look fully copied

    from pipeline import inbox as inbox_module

    inbox_module.process_inbox_once()

    artworks = client.get("/artworks/").json()
    assert len(artworks) == 2 and not any(a["classified"] for a in artworks)
    assert all(client.get(a["thumb_url"]).status_code == 200 for a in artworks)
    skipped = sorted(p.name for p in (inbox / "_skipped").rglob("*") if p.is_file())
    assert skipped == ["blue-copy.png", "broken.png", "notes.txt"]
    leftovers = [p.name for p in inbox.rglob("*") if p.is_file() and "_skipped" not in p.parts]
    assert leftovers == [".DS_Store"]  # hidden files are left alone


def test_desktop_worker_classifies_server_queue(start_app, monkeypatch, server, mixed_folder, tmp_path):
    url, _ = server
    for name in ("blue.png", "series/red.jpg"):
        httpx.post(f"{url}/artworks", files=[("files", (name, (mixed_folder / name).read_bytes()))])
    assert httpx.get(f"{url}/queue").json()["pending"] == 2

    monkeypatch.setenv("ATELIER_SERVER_URL", url)
    start_app(tmp_path / "local")
    from pipeline import worker

    with httpx.Client() as client:
        assert worker.process_queue_once(client) == 2
        assert worker.process_queue_once(client) == 0

    artworks = httpx.get(f"{url}/artworks/").json()
    assert all(a["classified"] and a["image_type"] == "painting" for a in artworks)
