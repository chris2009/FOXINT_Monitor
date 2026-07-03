from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageRead
from app.services.graph_api import GraphAPIClient, GraphAPIError, NotAPageError
from app.services.youtube import ChannelNotFoundError, YouTubeClient, YouTubeError

router = APIRouter()


async def _build_facebook_page(reference: str, poll_interval: int) -> Page:
    async with GraphAPIClient() as client:
        try:
            info = await client.validate_is_page(reference)
        except NotAPageError as exc:
            raise HTTPException(
                status_code=422, detail=f"Objetivo rechazado: no es una Página pública. {exc}"
            ) from exc
        except GraphAPIError as exc:
            raise HTTPException(status_code=502, detail=f"Error consultando Graph API: {exc}") from exc
    return Page(
        fb_page_id=info.id,
        name=info.name,
        category=info.category,
        platform="facebook",
        fan_count=info.fan_count,
        followers_count=info.followers_count,
        poll_interval=poll_interval,
    )


async def _build_youtube_page(reference: str, poll_interval: int) -> Page:
    async with YouTubeClient() as client:
        try:
            info = await client.resolve_channel(reference)
        except ChannelNotFoundError as exc:
            raise HTTPException(status_code=422, detail=f"Canal no encontrado. {exc}") from exc
        except YouTubeError as exc:
            raise HTTPException(status_code=502, detail=f"Error consultando YouTube API: {exc}") from exc
    return Page(
        fb_page_id=info.id,
        name=info.title,
        category="YouTube Channel",
        platform="youtube",
        followers_count=info.subscriber_count,
        poll_interval=poll_interval,
    )


@router.post("", response_model=PageRead, status_code=201)
async def register_page(payload: PageCreate, db: AsyncSession = Depends(get_db)) -> Page:
    """Registra un objetivo. Facebook valida Página/Perfil; YouTube resuelve el canal público."""
    if payload.platform == "youtube":
        page = await _build_youtube_page(payload.fb_page_id, payload.poll_interval)
    elif payload.platform == "facebook":
        page = await _build_facebook_page(payload.fb_page_id, payload.poll_interval)
    else:
        raise HTTPException(status_code=422, detail=f"Plataforma no soportada: {payload.platform}")

    # La deduplicación se hace con el ID canónico ya resuelto (no con lo que escribió el usuario).
    existing = await db.scalar(select(Page).where(Page.fb_page_id == page.fb_page_id))
    if existing:
        raise HTTPException(status_code=409, detail="El objetivo ya está registrado")

    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


@router.get("", response_model=list[PageRead])
async def list_pages(db: AsyncSession = Depends(get_db)) -> list[Page]:
    result = await db.scalars(select(Page).order_by(Page.created_at.desc()))
    return list(result.all())
