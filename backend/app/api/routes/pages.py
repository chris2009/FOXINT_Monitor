from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageRead
from app.services.graph_api import GraphAPIClient, GraphAPIError, NotAPageError

router = APIRouter()


@router.post("", response_model=PageRead, status_code=201)
async def register_page(payload: PageCreate, db: AsyncSession = Depends(get_db)) -> Page:
    """Registra un nuevo objetivo. Rechaza el registro si el ID no corresponde a una Página pública."""
    existing = await db.scalar(select(Page).where(Page.fb_page_id == payload.fb_page_id))
    if existing:
        raise HTTPException(status_code=409, detail="La página ya está registrada")

    async with GraphAPIClient() as client:
        try:
            page_info = await client.validate_is_page(payload.fb_page_id)
        except NotAPageError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Objetivo rechazado: no es una Página pública. {exc}",
            ) from exc
        except GraphAPIError as exc:
            raise HTTPException(status_code=502, detail=f"Error consultando Graph API: {exc}") from exc

    page = Page(
        fb_page_id=page_info.id,
        name=page_info.name,
        category=page_info.category,
        fan_count=page_info.fan_count,
        followers_count=page_info.followers_count,
        poll_interval=payload.poll_interval,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


@router.get("", response_model=list[PageRead])
async def list_pages(db: AsyncSession = Depends(get_db)) -> list[Page]:
    result = await db.scalars(select(Page).order_by(Page.created_at.desc()))
    return list(result.all())
