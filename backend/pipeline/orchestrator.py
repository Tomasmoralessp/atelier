"""Import pipeline: check files, classify them, then store them.

Storage goes to the local library, or, when ATELIER_SERVER_URL is set, to a
remote Atelier server (the NAS). Classification always runs on this machine.
"""

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import pipeline.categories
import pipeline.colors
import pipeline.hashing
import pipeline.remote
import settings
from database.models import Artwork, ArtworkColor
from pipeline.storage import FileType, get_file_extension, get_file_type
from pipeline.storage import is_readable_image, store_file

NUM_COLOR_PALETTE = 5

# The NAS server image ships without PyTorch/CLIP: images uploaded straight
# to it are stored with colors only and can be classified by hand.
CLIP_AVAILABLE = importlib.util.find_spec("open_clip") is not None


@dataclass
class ImportSummary:
    imported: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)


def _media_dir(file_type: FileType) -> Path:
    return settings.VIDEOS_DIR if file_type == FileType.video else settings.IMAGES_DIR


def _classify(images: list[dict]) -> None:
    """Fill image_type / subject / art_technique / colors in place."""
    for item in images:
        item["colors"] = pipeline.colors.process_and_extract_color_palette(
            image_path=item["source"], num_colors=NUM_COLOR_PALETTE
        )
    if not CLIP_AVAILABLE:
        return

    from pipeline import classification, embeddings as clip  # needs PyTorch

    embeddings = clip.generate_embeddings_batch(
        [item["source"] for item in images]
    )
    image_types = classification.classify_zero_shot_batch(
        embeddings, pipeline.categories.IMAGE_TYPE_PROMPTS
    )
    for item, image_type in zip(images, image_types):
        item["image_type"] = image_type["category"]

    for field_name, allowed_types, prompts in (
        ("subject", pipeline.categories.TYPES_WITH_SUBJECT,
         pipeline.categories.SUBJECT_PROMPTS),
        ("art_technique", pipeline.categories.TYPES_WITH_TECHNIQUE,
         pipeline.categories.ART_TECHNIQUE_PROMPTS),
    ):
        indices = [i for i, item in enumerate(images) if item["image_type"] in allowed_types]
        if indices:
            results = classification.classify_zero_shot_batch(
                [embeddings[i] for i in indices], prompts
            )
            for i, result in zip(indices, results):
                images[i][field_name] = result["category"]


def artwork_metadata(item: dict) -> dict:
    """The analysis result of one file, as stored and as sent to a server."""
    return {
        "id": item["id"],
        "file_type": item["file_type"].value,
        "file_extension": item["ext"].removeprefix("."),
        "image_type": item.get("image_type"),
        "subject": item.get("subject"),
        "art_technique": item.get("art_technique"),
        "colors": item.get("colors", []),
    }


def save_artwork(session: Session, metadata: dict, source: Path, copy: bool) -> None:
    """Put the file in the library and add its rows (caller commits)."""
    folder = "videos" if metadata["file_type"] == FileType.video.value else "images"
    relative = Path(folder) / f"{metadata['id']}.{metadata['file_extension']}"
    store_file(source, settings.DATA_DIR / relative, copy=copy)
    session.add(Artwork(
        id=metadata["id"],
        file_type=metadata["file_type"],
        file_extension=metadata["file_extension"],
        file_path=str(relative),
        image_type=metadata.get("image_type"),
        subject=metadata.get("subject"),
        art_technique=metadata.get("art_technique"),
    ))
    for color in metadata.get("colors", []):
        session.add(ArtworkColor(
            artwork_id=metadata["id"],
            r=color["rgb"][0], g=color["rgb"][1], b=color["rgb"][2],
            l_value=color["lab"][0], a_value=color["lab"][1], b_value=color["lab"][2],
            percentage=color["percentage"],
        ))


def artwork_exists(session: Session, artwork_id: str) -> bool:
    return session.execute(select(Artwork.id).where(Artwork.id == artwork_id)).first() is not None


def process_batch(
    file_paths: list[Path],
    session: Session,
    copy: bool,
    names: list[str] | None = None,
) -> ImportSummary:
    """Import files into the library.

    copy=True keeps the originals (folder import); copy=False moves them
    (uploaded temp files). names are the labels used in the summary.
    """
    names = names or [p.name for p in file_paths]
    summary = ImportSummary()
    seen_ids: set[str] = set()
    items = []

    for source, name in zip(file_paths, names):
        ext = get_file_extension(source)
        file_type = get_file_type(ext)
        if file_type == FileType.unknown:
            summary.skipped.append({"name": name, "reason": "not an image"})
            continue
        if file_type == FileType.image and not is_readable_image(source):
            summary.skipped.append({"name": name, "reason": "unreadable image"})
            continue

        file_id = pipeline.hashing.compute_hash(source)
        if file_id in seen_ids:
            summary.duplicates.append(name)
            continue
        seen_ids.add(file_id)
        items.append({"id": file_id, "source": source, "name": name, "ext": ext,
                      "file_type": file_type})

    # Ask the server in one go, so known files are not classified again.
    if settings.SERVER_URL:
        known = pipeline.remote.existing_ids([item["id"] for item in items])
    else:
        known = {item["id"] for item in items if artwork_exists(session, item["id"])}
    summary.duplicates += [item["name"] for item in items if item["id"] in known]
    items = [item for item in items if item["id"] not in known]

    images = [item for item in items if item["file_type"] == FileType.image]
    if images:
        _classify(images)

    if settings.SERVER_URL:
        for item in items:
            status = pipeline.remote.push(artwork_metadata(item), item["source"], item["name"])
            (summary.imported if status == "imported" else summary.duplicates).append(item["name"])
        return summary

    try:
        for item in items:
            save_artwork(session, artwork_metadata(item), item["source"], copy=copy)
            summary.imported.append(item["name"])
        session.commit()
    except Exception:
        session.rollback()
        raise
    return summary
