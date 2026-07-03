"""Entidades detectadas por el NER, agregadas para el panel de filtros (tipo INTELION).

Las entidades se guardan por post como detecciones (analyzer='ner', result.entities).
Aquí se agregan (conteo por entidad) y se listan los posts que mencionan una entidad.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.post import Post
from app.schemas.entity import EntityCount
from app.schemas.post import PostRead

router = APIRouter()

_AGG_SQL = text(
    """
    SELECT e->>'text' AS text, e->>'type' AS type, COUNT(*) AS count
    FROM detections d,
         jsonb_array_elements((d.result::jsonb)->'entities') AS e
    WHERE d.analyzer = 'ner'
      AND (CAST(:entity_type AS TEXT) IS NULL OR e->>'type' = CAST(:entity_type AS TEXT))
    GROUP BY 1, 2
    ORDER BY count DESC, text ASC
    LIMIT :limit
    """
)

_POSTS_BY_ENTITY_SQL = text(
    """
    SELECT DISTINCT d.post_id
    FROM detections d,
         jsonb_array_elements((d.result::jsonb)->'entities') AS e
    WHERE d.analyzer = 'ner'
      AND lower(e->>'text') = lower(:entity_text)
    """
)


@router.get("", response_model=list[EntityCount])
async def list_entities(
    entity_type: str | None = Query(None, description="Filtra por tipo: persona | lugar | organización"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[EntityCount]:
    rows = (await db.execute(_AGG_SQL, {"entity_type": entity_type, "limit": limit})).all()
    return [EntityCount(text=row.text, type=row.type, count=row.count) for row in rows]


@router.get("/posts", response_model=list[PostRead])
async def posts_for_entity(
    text_value: str = Query(..., alias="text", min_length=1, description="Entidad exacta a buscar"),
    db: AsyncSession = Depends(get_db),
) -> list[Post]:
    post_ids = list(await db.scalars(_POSTS_BY_ENTITY_SQL, {"entity_text": text_value}))
    if not post_ids:
        return []
    result = await db.scalars(select(Post).where(Post.id.in_(post_ids)).order_by(Post.captured_at.desc()))
    return list(result.all())
