"""Búsqueda por SIMILITUD facial sobre el corpus ya capturado.

Subes una imagen con una cara; el sistema detecta la cara, la convierte en vector y busca
caras parecidas entre las imágenes que YA capturó de las páginas monitoreadas. Es similitud
sobre un corpus acotado y autorizado — no identifica personas ni busca en la web abierta.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.post import Post
from app.schemas.face_search import FaceSearchResult
from app.schemas.post import PostRead
from app.services.face_embeddings import embed_face

router = APIRouter()

_SEARCH_SQL = text(
    """
    SELECT pf.post_id, pf.image_url, pf.bbox, (pf.embedding <=> (:qvec)::vector) AS distance
    FROM post_faces pf
    JOIN posts p ON p.id = pf.post_id
    WHERE (CAST(:page_id AS BIGINT) IS NULL OR p.page_id = CAST(:page_id AS BIGINT))
    ORDER BY distance ASC
    LIMIT :limit
    """
)


@router.post("", response_model=list[FaceSearchResult])
async def search_by_face(
    file: UploadFile = File(..., description="Imagen que contiene la cara de referencia"),
    page_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[FaceSearchResult]:
    image_bytes = await file.read()
    vector = await run_in_threadpool(embed_face, image_bytes)
    if vector is None:
        raise HTTPException(status_code=422, detail="No se detectó ninguna cara en la imagen subida.")

    qvec = "[" + ",".join(repr(float(x)) for x in vector) + "]"
    rows = (await db.execute(_SEARCH_SQL, {"qvec": qvec, "page_id": page_id, "limit": limit})).all()
    if not rows:
        return []

    posts = (await db.scalars(select(Post).where(Post.id.in_({row.post_id for row in rows})))).all()
    posts_by_id = {post.id: post for post in posts}

    return [
        FaceSearchResult(
            post=PostRead.model_validate(posts_by_id[row.post_id]),
            image_url=row.image_url,
            bbox=row.bbox,
            score=1.0 - row.distance,
        )
        for row in rows
        if row.post_id in posts_by_id
    ]
