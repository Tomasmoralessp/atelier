from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, HTTPException, Query
from sqlalchemy import select

from schemas.artwork import (
    ArtworkResponse,
    ArtworkUpdate,
    ArtworkFilter,
    ArtworkDeleteRequest,
    ImportSummaryResponse,
)
from sqlalchemy.orm import Session

import settings
from pipeline.orchestrator import process_batch
from pipeline.storage import save_upload_to_temp
from pipeline.colors import rgb_to_lab, lab_distance
from database.models import Artwork, ArtworkTag, ArtworkColor
from database.engine import get_session

MIN_COLOR_PERCENTAGE = 5.0


router = APIRouter(prefix="/artworks", tags=["artworks"])


@router.get("/extensions", response_model=list[str])
def list_extensions(session=Depends(get_session)):
    query = select(Artwork.file_extension).distinct()
    result = session.execute(query)
    return [row[0] for row in result]


@router.get("/", response_model=list[ArtworkResponse])
def list_artworks(
    filters: Annotated[ArtworkFilter, Query()], session=Depends(get_session)
):
    query = select(Artwork)
    if filters.file_type:
        if filters.file_type == "video":
            query = query.where(Artwork.file_type == "video")

        elif filters.file_type == "image":
            query = query.where(Artwork.file_type == "image")

            if filters.image_type:
                query = query.where(Artwork.image_type == filters.image_type)

            if filters.subject:
                query = query.where(Artwork.subject == filters.subject)

            if filters.art_technique:
                query = query.where(Artwork.art_technique == filters.art_technique)

            if filters.reviewed is not None:
                query = query.where(Artwork.reviewed == filters.reviewed)

    if filters.colors:
        colors_query = select(ArtworkColor).where(
            ArtworkColor.percentage >= MIN_COLOR_PERCENTAGE
        )
        all_candidates = session.execute(colors_query).scalars().all()
        matching_colors = None
        for color in filters.colors:
            color_array = list(map(int, color.split(",")))
            lab_color_array = rgb_to_lab(color_array)

            matching_artwork_ids = set()
            for candidate in all_candidates:
                candidate_lab = [
                    candidate.l_value,
                    candidate.a_value,
                    candidate.b_value,
                ]
                if (
                    lab_distance(candidate_lab, lab_color_array)
                    <= filters.color_threshold
                ):
                    matching_artwork_ids.add(candidate.artwork_id)

            if matching_colors is None:
                matching_colors = matching_artwork_ids
            else:
                matching_colors = matching_colors.intersection(matching_artwork_ids)

        query = query.where(Artwork.id.in_(matching_colors))

    if filters.tag_ids:
        query = query.join(ArtworkTag, Artwork.id == ArtworkTag.artwork_id).where(
            ArtworkTag.tag_id.in_(filters.tag_ids)
        )

    if filters.file_extension:
        query = query.where(Artwork.file_extension == f"{filters.file_extension}")

    result = session.execute(query)
    artworks = result.scalars().all()

    if not artworks:
        return []

    return [ArtworkResponse.model_validate(artwork) for artwork in artworks]


@router.get("/{artwork_id}", response_model=ArtworkResponse)
def get_artwork(artwork_id: str, session: Session = Depends(get_session)):
    query = select(Artwork).where(Artwork.id == artwork_id)
    result = session.execute(query)
    artwork = result.scalar_one_or_none()

    if not artwork:
        raise HTTPException(404, detail=f"Artwork with id {artwork_id} was not found.")

    return ArtworkResponse.model_validate(artwork)


@router.post("", response_model=ImportSummaryResponse)
async def post_artworks(
    files: list[UploadFile], session: Session = Depends(get_session)
):
    temp_paths = [
        await save_upload_to_temp(file=file, temp_dir=settings.TEMP_DIR)
        for file in files
    ]
    names = [file.filename or path.name for file, path in zip(files, temp_paths)]
    try:
        summary = process_batch(temp_paths, session, copy=False, names=names)
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)
    return ImportSummaryResponse.model_validate(summary, from_attributes=True)


@router.patch("/{artwork_id}", response_model=ArtworkResponse)
def update_artwork(
    artwork_id: str,
    update: Annotated[ArtworkUpdate, Query()],
    session: Session = Depends(get_session),
):
    artwork_query = select(Artwork).where(Artwork.id == artwork_id)
    artwork_result = session.execute(artwork_query)
    artwork = artwork_result.scalar_one_or_none()

    if not artwork:
        raise HTTPException(
            404, detail=f"ArtWork with id = {artwork_id} was not found."
        )

    if update.tag_ids is not None:
        existing_tags_query = select(ArtworkTag).where(
            ArtworkTag.artwork_id == artwork_id
        )
        existing_tags_result = session.execute(existing_tags_query)
        existing_tags = existing_tags_result.scalars().all()

        for tag in existing_tags:
            session.delete(tag)

        if update.tag_ids:
            for tag_id in update.tag_ids:
                artwork_tag = ArtworkTag(artwork_id=artwork.id, tag_id=tag_id)
                session.add(artwork_tag)

    if artwork.file_type == "video":
        pass

    elif artwork.file_type == "image":
        if update.subject:
            artwork.subject = update.subject

        if update.art_technique:
            artwork.art_technique = update.art_technique

        if update.image_type:
            artwork.image_type = update.image_type

    if update.reviewed is not None:
        artwork.reviewed = update.reviewed

    session.add(artwork)
    session.commit()

    return ArtworkResponse.model_validate(artwork)


@router.delete("/")
def delete_artworks(
    payload: ArtworkDeleteRequest, session=Depends(get_session)
) -> bool:
    for artwork_id in payload.artwork_ids:
        query = select(Artwork).where(Artwork.id == artwork_id)
        result = session.execute(query)
        artwork = result.scalar_one_or_none()
        if not artwork:
            raise HTTPException(
                404, detail=f"Artwork with id {artwork_id} was not found."
            )
        settings.resolve_media_path(artwork.file_path).unlink(missing_ok=True)
        session.delete(artwork)
    session.commit()
    return True
