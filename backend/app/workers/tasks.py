"""Tareas Celery: scheduler de polling, deduplicación y bus de analizadores.

Flujo (ver PROYECTO_OSINT_MONITOR.md, sección 3.1):
  dispatch_due_pages (beat, cada 60s)
    -> poll_page (por cada página cuyo poll_interval ya se cumplió)
      -> Graph API: /posts + /live_videos, deduplica contra platform_post_id
      -> process_post (por cada post nuevo)
        -> bus de analizadores (keyword, sentiment, live_detector)
        -> alertas a Telegram si corresponde
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers import get_analyzers
from app.db.sync_session import SyncSessionLocal
from app.models.alert import Alert
from app.models.detection import Detection
from app.models.embedding import PostEmbedding
from app.models.image_embedding import PostImageEmbedding
from app.models.keyword_rule import KeywordRule
from app.models.page import Page
from app.models.post import Post
from app.services.embeddings import embed_text
from app.services.graph_api import GraphAPIClient, GraphAPIError
from app.services.image_embeddings import embed_image
from app.services.telegram import TelegramNotifier
from app.workers.celery_app import celery_app

_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # no descargar imágenes de más de 10 MB


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _parse_dt(value: str | None) -> datetime | None:
    """Convierte timestamps de la Graph API (ej. '2024-01-01T12:00:00+0000') a datetime."""
    if not value:
        return None
    normalized = value
    if len(value) >= 5 and value[-5] in "+-" and value[-3] != ":":
        normalized = f"{value[:-2]}:{value[-2:]}"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _infer_post_type(item: dict[str, Any]) -> str:
    attachments = (item.get("attachments") or {}).get("data", [])
    if attachments:
        media_type = (attachments[0].get("media_type") or "").lower()
        if media_type in ("photo", "video"):
            return media_type
    return "status"


def _extract_media_urls(item: dict[str, Any]) -> list[str] | None:
    attachments = (item.get("attachments") or {}).get("data", [])
    urls = [a["media"]["image"]["src"] for a in attachments if a.get("media", {}).get("image")]
    return urls or None


async def _fetch_page_content(fb_page_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    async with GraphAPIClient() as client:
        posts = await client.get_posts(fb_page_id)
        live_videos = await client.get_live_videos(fb_page_id)
    return posts, live_videos


def _dispatch_alert(
    db: Session,
    post: Post,
    message: str,
    rule: KeywordRule | None,
    channels: list[str],
) -> None:
    notifier = TelegramNotifier()
    for channel in channels:
        db.add(Alert(post_id=post.id, rule_id=rule.id if rule else None, channel=channel, status="sent"))
        if channel == "telegram":
            _run_async(notifier.send_message(message))


@celery_app.task(name="osint.dispatch_due_pages")
def dispatch_due_pages() -> None:
    """Cada tick de beat: encola el polling de las páginas cuyo poll_interval ya se cumplió."""
    now = datetime.now(timezone.utc)
    with SyncSessionLocal() as db:
        pages = db.scalars(select(Page).where(Page.is_active.is_(True))).all()
        for page in pages:
            due = page.last_polled_at is None or (now - page.last_polled_at) >= timedelta(seconds=page.poll_interval)
            if due:
                poll_page.delay(page.id)


@celery_app.task(name="osint.poll_page")
def poll_page(page_id: int) -> None:
    """Consulta /posts + /live_videos de una página, deduplica y guarda los ítems nuevos."""
    now = datetime.now(timezone.utc)
    new_post_ids: list[int] = []

    with SyncSessionLocal() as db:
        page = db.get(Page, page_id)
        if page is None or not page.is_active:
            return

        try:
            posts_data, live_data = _run_async(_fetch_page_content(page.fb_page_id))
        except GraphAPIError:
            return  # el próximo tick reintenta; el rate-limit ya lo detecta el cliente

        live_by_id = {item["id"]: item for item in live_data}

        for item in posts_data:
            platform_post_id = item["id"]
            if db.scalar(select(Post.id).where(Post.platform_post_id == platform_post_id)):
                continue  # deduplicador: ya visto

            live_info = live_by_id.get(platform_post_id)
            post = Post(
                page_id=page.id,
                platform_post_id=platform_post_id,
                type="live" if live_info else _infer_post_type(item),
                message=item.get("message"),
                permalink=item.get("permalink_url"),
                media_urls=_extract_media_urls(item),
                is_live=bool(live_info),
                live_status=live_info["status"] if live_info else None,
                published_at=_parse_dt(item.get("created_time")),
            )
            db.add(post)
            db.flush()
            new_post_ids.append(post.id)

        # Directos que arrancaron sin post asociado todavía en /posts
        for live_item in live_data:
            if db.scalar(select(Post.id).where(Post.platform_post_id == live_item["id"])):
                continue
            post = Post(
                page_id=page.id,
                platform_post_id=live_item["id"],
                type="live",
                message=live_item.get("title"),
                permalink=live_item.get("permalink_url"),
                is_live=True,
                live_status=live_item.get("status"),
                published_at=_parse_dt(live_item.get("creation_time")),
            )
            db.add(post)
            db.flush()
            new_post_ids.append(post.id)

        page.last_polled_at = now
        db.commit()

    for post_id in new_post_ids:
        process_post.delay(post_id)


@celery_app.task(name="osint.process_post")
def process_post(post_id: int) -> None:
    """Corre el bus de analizadores sobre un post nuevo y dispara alertas si corresponde."""
    with SyncSessionLocal() as db:
        post = db.get(Post, post_id)
        if post is None:
            return

        active_rules = list(db.scalars(select(KeywordRule).where(KeywordRule.is_active.is_(True))))
        rules_by_id = {rule.id: rule for rule in active_rules}
        context = {"keyword_rules": active_rules}

        for analyzer in get_analyzers():
            detection = _run_async(analyzer.analyze(post, context))
            if detection is None:
                continue

            db.add(
                Detection(
                    post_id=post.id,
                    analyzer=detection.analyzer,
                    result=detection.result,
                    score=detection.score,
                )
            )

            if detection.analyzer == "keyword":
                for match in detection.result["matches"]:
                    rule = rules_by_id[match["rule_id"]]
                    message = f"[{rule.severity.upper()}] Regla '{rule.label}' en {post.page.name}: {post.permalink}"
                    _dispatch_alert(db, post, message, rule=rule, channels=rule.notify_channels)
            elif detection.analyzer == "live_detector":
                message = f"Live iniciado en {post.page.name}: {post.permalink}"
                _dispatch_alert(db, post, message, rule=None, channels=["telegram"])

        _index_embedding(db, post)
        _index_image_embeddings(db, post)
        db.commit()


def _index_embedding(db: Session, post: Post) -> None:
    """Genera y guarda el vector semántico del post, para la búsqueda por similitud (/api/search)."""
    if not (post.message and post.message.strip()):
        return
    if db.scalar(select(PostEmbedding.post_id).where(PostEmbedding.post_id == post.id)):
        return  # ya indexado

    vector = _run_async(embed_text(post.message[:2000]))
    db.add(PostEmbedding(post_id=post.id, embedding=vector))


def _download_image(url: str) -> bytes | None:
    # Muchos CDNs (incl. Wikimedia) rechazan peticiones sin User-Agent con 403.
    headers = {"User-Agent": "FoxintMonitor/0.1 (OSINT monitor; local research)"}
    try:
        response = httpx.get(url, timeout=15.0, follow_redirects=True, headers=headers)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    content = response.content
    if not content or len(content) > _MAX_IMAGE_BYTES:
        return None
    return content


def _index_image_embeddings(db: Session, post: Post) -> None:
    """Descarga y embebe (CLIP) cada imagen del post, para la búsqueda visual (/api/search/images)."""
    for url in post.media_urls or []:
        if db.scalar(
            select(PostImageEmbedding.id).where(
                PostImageEmbedding.post_id == post.id, PostImageEmbedding.image_url == url
            )
        ):
            continue  # ya indexada

        image_bytes = _download_image(url)
        if image_bytes is None:
            continue
        try:
            vector = embed_image(image_bytes)
        except Exception:
            continue  # imagen corrupta o formato no soportado: se omite sin romper la tarea
        db.add(PostImageEmbedding(post_id=post.id, image_url=url, embedding=vector))
