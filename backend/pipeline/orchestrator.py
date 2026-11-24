from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import select

import pipeline.hashing
import pipeline.storage
import pipeline.colors
import pipeline.embeddings
import pipeline.classification
import pipeline.categories

from database.models import Artwork, ArtworkColor


ATELIER_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

IMAGES_DIR = ATELIER_DATA_DIR / "images"
VIDEOS_DIR = ATELIER_DATA_DIR / "videos"
UNKNOWN_DIR = ATELIER_DATA_DIR / "unknown"
TEMP_DIR = ATELIER_DATA_DIR / "temp"


class Orchestrator:
    def __init__(self, image_dir: Path, video_dir: Path, unknown_dir: Path):
        self.image_dir = image_dir
        self.video_dir = video_dir
        self.unknown_dir = unknown_dir
        self.num_color_palette = 5

    def save_artwork(self, session, artwork_data: dict) -> None:
        new_artwork = Artwork(**artwork_data)
        session.add(new_artwork)

    def save_artwork_color(self, session, artwork_color_data: dict) -> None:
        new_artwork_color = ArtworkColor(**artwork_color_data)
        session.add(new_artwork_color)

    def get_file_id(self, file_path: Path) -> str:
        file_id = pipeline.hashing.compute_hash(file_path)
        return file_id

    def get_file_info(self, file_path: Path) -> tuple[str, pipeline.storage.FileType]:
        ext = pipeline.storage.get_file_extension(file_path)

        file_type = pipeline.storage.get_file_type(ext)

        return ext, file_type

    def move_to_storage(
        self,
        file_id: str,
        file_path: Path,
        file_extension: str,
        file_type: pipeline.storage.FileType,
    ) -> str:
        file_destination = pipeline.storage.move_to_storage(
            file_id=file_id,
            file_path=file_path,
            file_extension=file_extension,
            file_type=file_type,
            image_dir=self.image_dir,
            video_dir=self.video_dir,
            unknown_dir=self.unknown_dir,
        )
        return file_destination

    def get_color_palette(self, image_path: Path) -> list[dict]:
        return pipeline.colors.process_and_extract_color_palette(
            image_path=image_path, num_colors=self.num_color_palette
        )

    def generate_embeddings(self, image_paths: list[Path]) -> list:
        return pipeline.embeddings.generate_embeddings_batch(image_paths=image_paths)

    def get_image_types(self, image_embeddings: list) -> list[dict]:
        return pipeline.classification.classify_zero_shot_batch(
            image_embeddings=image_embeddings,
            category_prompts=pipeline.categories.IMAGE_TYPE_PROMPTS,
        )

    def get_subjects(self, image_embeddings: list) -> list[dict]:
        return pipeline.classification.classify_zero_shot_batch(
            image_embeddings=image_embeddings,
            category_prompts=pipeline.categories.SUBJECT_PROMPTS,
        )

    def get_art_technique(self, image_embeddings: list) -> list[dict]:
        return pipeline.classification.classify_zero_shot_batch(
            image_embeddings=image_embeddings,
            category_prompts=pipeline.categories.ART_TECHNIQUE_PROMPTS,
        )

    def is_artwork_duplicated(self, file_id: str, session: Session) -> bool:
        query = select(Artwork).where(Artwork.id == file_id)
        result = session.execute(query)
        artwork = result.scalar_one_or_none()

        return artwork is not None

    def process_batch(self, file_paths: list[Path], session: Session):
        try:
            images_data = []
            for file_path in file_paths:
                file_id = self.get_file_id(file_path=file_path)

                if self.is_artwork_duplicated(file_id=file_id, session=session):
                    pass
                else:
                    file_extension, file_type = self.get_file_info(file_path)

                    if file_type == pipeline.storage.FileType.image:
                        images_data.append(
                            {
                                "id": file_id,
                                "file_type": file_type,
                                "file_path": file_path,
                                "image_type": file_type,
                                "file_extension": file_extension,
                            }
                        )

                    elif file_type == pipeline.storage.FileType.video:
                        file_destination = self.move_to_storage(
                            file_id=file_id,
                            file_path=file_path,
                            file_extension=file_extension,
                            file_type=file_type,
                        )
                        artwork_data = {
                            "id": file_id,
                            "file_type": "video",
                            "file_extension": file_extension.removeprefix("."),
                            "file_path": file_destination,
                        }
                        self.save_artwork(session, artwork_data)

                    elif file_type == pipeline.storage.FileType.unknown:
                        # TODO:Error control
                        self.move_to_storage(
                            file_id=file_id,
                            file_path=file_path,
                            file_extension=file_extension,
                            file_type=file_type,
                        )

            image_paths = [item["file_path"] for item in images_data]

            if image_paths:
                embeddings = self.generate_embeddings(image_paths)
                image_types = self.get_image_types(embeddings)
                for i, item in enumerate(images_data):
                    item["embedding"] = embeddings[i]
                    item["image_type"] = image_types[i]["category"]
                    item["image_type_confidence"] = image_types[i]["confidence"]
                    item["color_palette"] = self.get_color_palette(item["file_path"])

                items_needing_subject = [
                    item
                    for item in images_data
                    if item["image_type"] in pipeline.categories.TYPES_WITH_SUBJECT
                ]

                if items_needing_subject:
                    subject_embeddings = [
                        item["embedding"] for item in items_needing_subject
                    ]
                    subjects = self.get_subjects(subject_embeddings)
                    for item, subject_result in zip(items_needing_subject, subjects):
                        item["subject"] = subject_result["category"]
                        item["subject_confidence"] = subject_result["confidence"]

                items_with_technique = [
                    item
                    for item in images_data
                    if item["image_type"] in pipeline.categories.TYPES_WITH_TECHNIQUE
                ]

                if items_with_technique:
                    technique_embeddings = [
                        item["embedding"] for item in items_with_technique
                    ]
                    techniques = self.get_art_technique(technique_embeddings)
                    for item, technique_result in zip(items_with_technique, techniques):
                        item["art_technique"] = technique_result["category"]
                        item["technique_confidence"] = technique_result["confidence"]

                for item in images_data:
                    file_destination = self.move_to_storage(
                        file_path=item["file_path"],
                        file_id=item["id"],
                        file_extension=item["file_extension"],
                        file_type=item["file_type"],
                    )
                    artwork_data = {
                        "id": item["id"],
                        "file_type": item["file_type"].value,
                        "file_extension": item["file_extension"].removeprefix("."),
                        "file_path": str(file_destination),
                        "image_type": item["image_type"],
                        "subject": item.get("subject"),
                        "art_technique": item.get("art_technique"),
                    }
                    self.save_artwork(session, artwork_data)
                    for color in item["color_palette"]:
                        artwork_color = {
                            "artwork_id": item["id"],
                            "r": color["rgb"][0],
                            "g": color["rgb"][1],
                            "b": color["rgb"][2],
                            "l_value": color["lab"][0],
                            "a_value": color["lab"][1],
                            "b_value": color["lab"][2],
                            "percentage": color["percentage"],
                        }
                        self.save_artwork_color(session, artwork_color)

            session.commit()

        except Exception:
            session.rollback()
            raise


orchestrator_object = Orchestrator(IMAGES_DIR, VIDEOS_DIR, UNKNOWN_DIR)
