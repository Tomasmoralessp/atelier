from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import pipeline.categories
import pipeline.classification
import pipeline.colors
import pipeline.embeddings
import pipeline.hashing
import settings
from database.models import Artwork, ArtworkColor
from pipeline.storage import FileType, get_file_extension, get_file_type
from pipeline.storage import is_readable_image, store_file

NUM_COLOR_PALETTE = 5


@dataclass
class ImportSummary:
    imported: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)

    def merge(self, other: "ImportSummary") -> None:
        self.imported += other.imported
        self.duplicates += other.duplicates
        self.skipped += other.skipped


def _media_dir(file_type: FileType) -> Path:
    return settings.VIDEOS_DIR if file_type == FileType.video else settings.IMAGES_DIR


def _classify(images: list[dict]) -> None:
    """Fill image_type / subject / art_technique / colors in place."""
    embeddings = pipeline.embeddings.generate_embeddings_batch(
        [item["source"] for item in images]
    )
    image_types = pipeline.classification.classify_zero_shot_batch(
        embeddings, pipeline.categories.IMAGE_TYPE_PROMPTS
    )
    for item, embedding, image_type in zip(images, embeddings, image_types):
        item["embedding"] = embedding
        item["image_type"] = image_type["category"]
        item["colors"] = pipeline.colors.process_and_extract_color_palette(
            image_path=item["source"], num_colors=NUM_COLOR_PALETTE
        )

    for field_name, allowed_types, prompts in (
        ("subject", pipeline.categories.TYPES_WITH_SUBJECT,
         pipeline.categories.SUBJECT_PROMPTS),
        ("art_technique", pipeline.categories.TYPES_WITH_TECHNIQUE,
         pipeline.categories.ART_TECHNIQUE_PROMPTS),
    ):
        targets = [item for item in images if item["image_type"] in allowed_types]
        if targets:
            results = pipeline.classification.classify_zero_shot_batch(
                [item["embedding"] for item in targets], prompts
            )
            for item, result in zip(targets, results):
                item[field_name] = result["category"]


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
    images, videos = [], []

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
        is_known = session.execute(
            select(Artwork.id).where(Artwork.id == file_id)
        ).first()
        if file_id in seen_ids or is_known:
            summary.duplicates.append(name)
            continue
        seen_ids.add(file_id)

        item = {"id": file_id, "source": source, "name": name, "ext": ext,
                "file_type": file_type}
        (images if file_type == FileType.image else videos).append(item)

    try:
        if images:
            _classify(images)

        for item in images + videos:
            file_type = item["file_type"]
            relative = Path(_media_dir(file_type).name) / f"{item['id']}{item['ext']}"
            store_file(item["source"], settings.DATA_DIR / relative, copy=copy)
            session.add(Artwork(
                id=item["id"],
                file_type=file_type.value,
                file_extension=item["ext"].removeprefix("."),
                file_path=str(relative),
                image_type=item.get("image_type"),
                subject=item.get("subject"),
                art_technique=item.get("art_technique"),
            ))
            for color in item.get("colors", []):
                session.add(ArtworkColor(
                    artwork_id=item["id"],
                    r=color["rgb"][0], g=color["rgb"][1], b=color["rgb"][2],
                    l_value=color["lab"][0], a_value=color["lab"][1],
                    b_value=color["lab"][2],
                    percentage=color["percentage"],
                ))
            summary.imported.append(item["name"])
        session.commit()
    except Exception:
        session.rollback()
        raise

    return summary
