"""Búsqueda visual sobre las imágenes ya capturadas (CLIP + pgvector).

Dos modos, ambos sobre el mismo espacio vectorial de CLIP:
  - GET  /api/search/images?q=texto   -> texto → imagen (encoder de texto multilingüe).
  - POST /api/search/images  (archivo) -> imagen → imagen (encoder de imágenes).
"""

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.post import Post
from app.schemas.image_search import ImageSearchResult
from app.schemas.post import PostRead
from app.services.image_embeddings import embed_image, embed_text_clip

router = APIRouter()

_SEARCH_SQL = text(
    """
    SELECT pie.post_id, pie.image_url, (pie.embedding <=> (:qvec)::vector) AS distance
    FROM post_image_embeddings pie
    JOIN posts p ON p.id = pie.post_id
    WHERE (CAST(:page_id AS BIGINT) IS NULL OR p.page_id = CAST(:page_id AS BIGINT))
    ORDER BY distance ASC
    LIMIT :limit
    """
)


async def _run_search(vector: list[float], page_id: int | None, limit: int, db: AsyncSession) -> list[ImageSearchResult]:
    qvec = "[" + ",".join(repr(float(x)) for x in vector) + "]"
    rows = (await db.execute(_SEARCH_SQL, {"qvec": qvec, "page_id": page_id, "limit": limit})).all()
    if not rows:
        return []

    posts = (await db.scalars(select(Post).where(Post.id.in_({row.post_id for row in rows})))).all()
    posts_by_id = {post.id: post for post in posts}

    results = [
        ImageSearchResult(
            post=PostRead.model_validate(posts_by_id[row.post_id]),
            image_url=row.image_url,
            score=1.0 - row.distance,
        )
        for row in rows
        if row.post_id in posts_by_id
    ]
    return results


@router.get("", response_model=list[ImageSearchResult])
async def search_images_by_text(
    q: str = Query(..., min_length=1, description="Descripción de lo que buscas en las imágenes"),
    page_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ImageSearchResult]:
    vector = await run_in_threadpool(embed_text_clip, q)
    return await _run_search(vector, page_id, limit, db)


@router.post("", response_model=list[ImageSearchResult])
async def search_images_by_image(
    file: UploadFile = File(..., description="Imagen de referencia"),
    page_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ImageSearchResult]:
    image_bytes = await file.read()
    vector = await run_in_threadpool(embed_image, image_bytes)
    return await _run_search(vector, page_id, limit, db)
