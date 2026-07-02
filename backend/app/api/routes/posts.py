from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.detection import Detection
from app.models.post import Post
from app.schemas.detection import DetectionRead
from app.schemas.post import PostRead

router = APIRouter()


@router.get("/pages/{page_id}/posts", response_model=list[PostRead], tags=["posts"])
async def list_posts_by_page(page_id: int, db: AsyncSession = Depends(get_db)) -> list[Post]:
    result = await db.scalars(
        select(Post).where(Post.page_id == page_id).order_by(Post.captured_at.desc())
    )
    return list(result.all())


@router.get("/posts/{post_id}/detections", response_model=list[DetectionRead], tags=["posts"])
async def list_post_detections(post_id: int, db: AsyncSession = Depends(get_db)) -> list[Detection]:
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    result = await db.scalars(
        select(Detection).where(Detection.post_id == post_id).order_by(Detection.created_at.desc())
    )
    return list(result.all())
