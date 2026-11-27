"""The classification queue.

Artworks stored without classification (uploaded straight to the NAS, or
dropped in its inbox folder) have classified=False. Desktop apps poll
GET /queue, classify the files on their own machine and send the result
back with PUT /artworks/{id}/analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from database.engine import get_session
from database.models import Artwork, ArtworkColor
from pipeline.orchestrator import add_colors
from schemas.artwork import ArtworkAnalysis, ArtworkResponse

router = APIRouter(tags=["queue"])


@router.get("/queue")
def get_queue(limit: int = Query(8, ge=0, le=64), session: Session = Depends(get_session)):
    pending = select(Artwork).where(Artwork.classified.is_(False))
    count = session.execute(select(func.count()).select_from(pending.subquery())).scalar_one()
    items = session.execute(pending.limit(limit)).scalars().all()
    return {
        "pending": count,
        "items": [ArtworkResponse.model_validate(a).model_dump(mode="json") for a in items],
    }


@router.put("/artworks/{artwork_id}/analysis", response_model=ArtworkResponse)
def set_analysis(
    artwork_id: str, analysis: ArtworkAnalysis, session: Session = Depends(get_session)
):
    artwork = session.get(Artwork, artwork_id)
    if artwork is None:
        raise HTTPException(404, detail=f"Artwork with id {artwork_id} was not found.")
    # Never overwrite what a person already reviewed.
    if not artwork.reviewed:
        artwork.image_type = analysis.image_type
        artwork.subject = analysis.subject
        artwork.art_technique = analysis.art_technique
    session.execute(delete(ArtworkColor).where(ArtworkColor.artwork_id == artwork_id))
    add_colors(session, artwork_id, [c.model_dump() for c in analysis.colors])
    artwork.classified = True
    session.commit()
    session.refresh(artwork)
    return ArtworkResponse.model_validate(artwork)
