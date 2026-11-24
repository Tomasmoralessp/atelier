from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from database.models import Tag
from schemas.tags import TagCreate, TagResponse
from database.engine import get_session


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagResponse])
def list_tags(session=Depends(get_session)):
    tags_query = select(Tag)
    tags_result = session.execute(tags_query)
    tags = tags_result.scalars().all()

    return [TagResponse.model_validate(tag) for tag in tags]


@router.post("/", response_model=TagResponse)
def create_tag(tag_create: TagCreate, session=Depends(get_session)):
    tag_query = select(Tag).where(Tag.name == tag_create.name)
    tag_result = session.execute(tag_query)
    tag = tag_result.scalar_one_or_none()

    if tag:
        return TagResponse.model_validate(tag)

    else:
        new_tag = Tag(name=tag_create.name)
        session.add(new_tag)
        session.commit()
        return TagResponse.model_validate(new_tag)


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, session=Depends(get_session)):
    tag_query = select(Tag).where(Tag.id == tag_id)
    tag_result = session.execute(tag_query)
    tag = tag_result.scalar_one_or_none()

    if not tag:
        raise HTTPException(404, detail=f"Tag with id = {tag_id} was not found.")

    if tag:
        session.delete(tag)
        session.commit()
        return True
