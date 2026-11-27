import importlib
import socket
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

OWN_MODULES = ("settings", "main", "database", "api", "pipeline", "schemas")


def _fresh_import_main():
    """Settings are read at import time, so each 'app start' re-imports
    our modules (third-party ones stay cached)."""
    for name in list(sys.modules):
        if name.split(".")[0] in OWN_MODULES:
            del sys.modules[name]
    return importlib.import_module("main")


def fake_classify(images: list[dict]) -> None:
    """Stand-in for CLIP so tests are fast and never need model weights."""
    for item in images:
        item["image_type"] = "painting"
        item["subject"] = "landscape"
        item["art_technique"] = "watercolor"
        item["colors"] = [{"rgb": [10, 20, 30], "lab": [7.0, 0.5, -10.0], "percentage": 100.0}]


@pytest.fixture
def no_network(monkeypatch):
    """Fail loudly if anything tries to open a network connection."""

    def guard(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)
    monkeypatch.setattr(socket, "getaddrinfo", guard)


@pytest.fixture
def start_app(monkeypatch, tmp_path):
    """start_app(data_dir=None) -> TestClient for a freshly started backend."""
    monkeypatch.setenv("ATELIER_MODE", "local")
    monkeypatch.delenv("ATELIER_MODEL_PATH", raising=False)

    def start(data_dir: Path | None = None, fake_model: bool = True) -> TestClient:
        monkeypatch.setenv("ATELIER_DATA_DIR", str(data_dir or tmp_path / "library"))
        main = _fresh_import_main()
        if fake_model:
            import pipeline.orchestrator

            monkeypatch.setattr(pipeline.orchestrator, "_classify", fake_classify)
        return TestClient(main.app)

    return start


@pytest.fixture
def mixed_folder(tmp_path) -> Path:
    folder = tmp_path / "artwork"
    (folder / "series").mkdir(parents=True)
    Image.new("RGB", (64, 64), (30, 80, 200)).save(folder / "blue.png")
    Image.new("RGB", (64, 64), (200, 40, 40)).save(folder / "series" / "red.jpg")
    Image.new("RGB", (64, 64), (30, 80, 200)).save(folder / "series" / "blue-copy.png")
    (folder / "notes.txt").write_text("not an image")
    (folder / "broken.png").write_text("not really a png")
    (folder / ".DS_Store").write_bytes(b"\0")
    return folder
