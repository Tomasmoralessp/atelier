import os

import pytest

pytestmark = pytest.mark.usefixtures("no_network")


def import_folder(client, folder):
    scan = client.post("/import/scan", json={"folder": str(folder)})
    assert scan.status_code == 200
    scan = scan.json()
    result = client.post("/import/files", json={"paths": scan["files"]})
    assert result.status_code == 200
    return scan, result.json()


def test_starts_without_network(start_app):
    client = start_app()
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["mode"] == "local"
    assert client.get("/artworks/").json() == []
    assert client.get("/tags/").json() == []


def test_first_run_creates_database_and_folders(start_app, tmp_path):
    data_dir = tmp_path / "brand new" / "Atelier"
    assert not data_dir.exists()

    start_app(data_dir)

    assert (data_dir / "atelier.db").is_file()
    for sub in ("images", "videos", "temp", "models"):
        assert (data_dir / sub).is_dir()


def test_import_mixed_folder(start_app, mixed_folder, tmp_path):
    client = start_app()
    scan, summary = import_folder(client, mixed_folder)

    assert [s["name"] for s in scan["skipped"]] == ["notes.txt"]
    assert sorted(summary["imported"]) == ["blue.png", "red.jpg"]
    assert summary["duplicates"] == ["blue-copy.png"]
    assert summary["skipped"] == [{"name": "broken.png", "reason": "unreadable image"}]

    artworks = client.get("/artworks/").json()
    assert len(artworks) == 2
    for artwork in artworks:
        assert not os.path.isabs(artwork["file_path"])
        assert (tmp_path / "library" / artwork["file_path"]).is_file()
        assert client.get(artwork["file_url"]).status_code == 200

    # Originals are copied, never moved.
    assert (mixed_folder / "blue.png").is_file()

    # Importing the same folder again only reports duplicates.
    _, again = import_folder(client, mixed_folder)
    assert again["imported"] == []
    assert len(again["duplicates"]) == 3


def test_data_persists_across_restarts(start_app, mixed_folder, tmp_path):
    data_dir = tmp_path / "library"
    client = start_app(data_dir)
    import_folder(client, mixed_folder)
    tag = client.post("/tags/", json={"name": "favourites"}).json()
    artwork_id = client.get("/artworks/").json()[0]["id"]
    client.patch(f"/artworks/{artwork_id}", params={"tag_ids": [tag["id"]], "reviewed": True})

    restarted = start_app(data_dir)

    artworks = {a["id"]: a for a in restarted.get("/artworks/").json()}
    assert len(artworks) == 2
    assert artworks[artwork_id]["reviewed"] is True
    assert [t["name"] for t in artworks[artwork_id]["tags"]] == ["favourites"]
    assert restarted.get(artworks[artwork_id]["file_url"]).status_code == 200


def test_upload_reports_summary_and_cleans_temp(start_app, mixed_folder, tmp_path):
    client = start_app()
    files = [
        ("files", ("blue.png", (mixed_folder / "blue.png").read_bytes(), "image/png")),
        ("files", ("notes.txt", b"hello", "text/plain")),
    ]
    summary = client.post("/artworks", files=files).json()
    assert summary["imported"] == ["blue.png"]
    assert summary["skipped"] == [{"name": "notes.txt", "reason": "not an image"}]
    assert list((tmp_path / "library" / "temp").iterdir()) == []


def test_delete_removes_file(start_app, mixed_folder, tmp_path):
    client = start_app()
    import_folder(client, mixed_folder)
    artwork = client.get("/artworks/").json()[0]
    stored = tmp_path / "library" / artwork["file_path"]

    assert client.request("DELETE", "/artworks/", json={"artwork_ids": [artwork["id"]]}).json()
    assert not stored.exists()


def test_backup_copies_database_and_media(start_app, mixed_folder, tmp_path):
    client = start_app()
    import_folder(client, mixed_folder)
    target = tmp_path / "nas-share"
    target.mkdir()

    first = client.post("/backup", json={"destination": str(target)}).json()
    second = client.post("/backup", json={"destination": str(target)}).json()

    backup_dir = target / "Atelier Backup"
    assert first["files_copied"] == 2
    assert second["files_copied"] == 0  # incremental
    assert (backup_dir / "atelier.db").is_file()
    assert len(list((backup_dir / "images").iterdir())) == 2

    # The backup is a working library on its own.
    restored = start_app(backup_dir)
    assert len(restored.get("/artworks/").json()) == 2


def test_folder_import_and_backup_disabled_in_remote_mode(start_app, monkeypatch, tmp_path):
    monkeypatch.setenv("ATELIER_MODE", "remote")
    client = start_app()
    assert client.post("/import/scan", json={"folder": str(tmp_path)}).status_code == 403
    assert client.post("/backup", json={"destination": str(tmp_path)}).status_code == 403


def test_rejects_path_traversal(start_app):
    client = start_app()
    assert client.get("/images/..%2Fatelier.db").status_code in (400, 404)


@pytest.mark.skipif(
    not os.environ.get("ATELIER_TEST_MODEL_PATH"),
    reason="set ATELIER_TEST_MODEL_PATH to bundled weights to run the real model",
)
def test_real_model_classifies_offline(start_app, mixed_folder, monkeypatch):
    monkeypatch.setenv("ATELIER_MODEL_PATH", os.environ["ATELIER_TEST_MODEL_PATH"])
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    client = start_app(fake_model=False)
    _, summary = import_folder(client, mixed_folder)
    assert sorted(summary["imported"]) == ["blue.png", "red.jpg"]
    assert all(a["image_type"] for a in client.get("/artworks/").json())
