"""Búsqueda semántica sobre los posts ya capturados (pgvector).

Embebe la consulta del usuario con nomic-embed-text y la compara por distancia
coseno contra los embeddings almacenados. Se puede acotar a una página concreta
con `page_id`, o buscar a través de todas las páginas monitoreadas.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.post import Post
from app.schemas.post import PostRead
from app.schemas.search import SearchResult
from app.services.embeddings import embed_text

router = APIRouter()

_SEARCH_SQL = text(
    """
    SELECT pe.post_id, (pe.embedding <=> (:qvec)::vector) AS distance
    FROM post_embeddings pe
    JOIN posts p ON p.id = pe.post_id
    WHERE (CAST(:page_id AS BIGINT) IS NULL OR p.page_id = CAST(:page_id AS BIGINT))
    ORDER BY distance ASC
    LIMIT :limit
    """
)


@router.get("", response_model=list[SearchResult])
async def semantic_search(
    q: str = Query(..., min_length=1, description="Texto a buscar"),
    page_id: int | None = Query(None, description="Acota la búsqueda a una página"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    vector = await embed_text(q, is_query=True)
    # Se pasa el vector como texto '[...]' y se castea a ::vector para evitar
    # ambigüedades de tipo del parámetro con el driver asyncpg.
    qvec = "[" + ",".join(repr(float(x)) for x in vector) + "]"

    rows = (await db.execute(_SEARCH_SQL, {"qvec": qvec, "page_id": page_id, "limit": limit})).all()
    if not rows:
        return []

    distance_by_id = {row.post_id: row.distance for row in rows}
    posts = (await db.scalars(select(Post).where(Post.id.in_(distance_by_id.keys())))).all()

    results = [
        SearchResult(post=PostRead.model_validate(post), score=1.0 - distance_by_id[post.id])
        for post in posts
    ]
    results.sort(key=lambda result: result.score, reverse=True)
    return results
