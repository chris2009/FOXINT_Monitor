"""Cliente async para la YouTube Data API v3 (acceso oficial a canales/videos públicos).

Espejo conceptual del cliente de Graph API: valida que la referencia sea un canal público
real y trae sus videos recientes. Un canal de YouTube se monitorea igual que una Página de
Facebook — la única diferencia es el conector de ingesta.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.services.youtube.exceptions import ChannelNotFoundError, YouTubeError

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

_CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")
_URL_CHANNEL_ID_RE = re.compile(r"youtube\.com/channel/(UC[\w-]{22})")
_URL_HANDLE_RE = re.compile(r"youtube\.com/@([\w.-]+)")
_URL_USER_RE = re.compile(r"youtube\.com/(?:c|user)/([\w.-]+)")


@dataclass(frozen=True)
class ChannelInfo:
    id: str
    title: str
    subscriber_count: int | None


class YouTubeClient:
    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self._api_key = api_key or settings.youtube_api_key
        self._client = httpx.AsyncClient(base_url=YOUTUBE_API_BASE_URL, timeout=timeout)

    async def __aenter__(self) -> "YouTubeClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._client.aclose()

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise YouTubeError("Falta YOUTUBE_API_KEY en la configuración.")
        response = await self._client.get(path, params={"key": self._api_key, **params})
        payload = response.json()
        if "error" in payload:
            message = payload["error"].get("message", "Error desconocido de YouTube API")
            raise YouTubeError(f"YouTube API error: {message}")
        return payload

    async def resolve_channel(self, reference: str) -> ChannelInfo:
        """Resuelve un canal público a partir de su ID (UC...), handle (@nombre) o URL."""
        reference = reference.strip()
        params: dict[str, Any] = {"part": "snippet,statistics"}

        if _CHANNEL_ID_RE.match(reference):
            params["id"] = reference
        elif match := _URL_CHANNEL_ID_RE.search(reference):
            params["id"] = match.group(1)
        elif match := _URL_HANDLE_RE.search(reference):
            params["forHandle"] = match.group(1)
        elif reference.startswith("@"):
            params["forHandle"] = reference[1:]
        elif match := _URL_USER_RE.search(reference):
            params["forUsername"] = match.group(1)
        else:
            # Sin prefijo reconocible: se intenta como handle.
            params["forHandle"] = reference

        data = await self._get("/channels", params)
        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(
                f"No se encontró un canal público para '{reference}' (¿handle/ID/URL correcto?)."
            )

        item = items[0]
        stats = item.get("statistics", {})
        subs = stats.get("subscriberCount")
        return ChannelInfo(
            id=item["id"],
            title=item["snippet"]["title"],
            subscriber_count=int(subs) if subs is not None and not stats.get("hiddenSubscriberCount") else None,
        )

    async def get_recent_videos(self, channel_id: str, limit: int = 25) -> list[dict[str, Any]]:
        """Videos recientes del canal, vía su playlist de subidas (más barato en cuota que search)."""
        # Truco documentado: la playlist de subidas es "UU" + el ID del canal sin el prefijo "UC".
        uploads_playlist = "UU" + channel_id[2:]
        data = await self._get(
            "/playlistItems",
            {"part": "snippet,contentDetails", "playlistId": uploads_playlist, "maxResults": limit},
        )

        videos: list[dict[str, Any]] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("contentDetails", {}).get("videoId")
            if not video_id:
                continue
            thumbnails = snippet.get("thumbnails", {})
            thumb = (thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}).get("url")
            videos.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail": thumb,
                }
            )
        return videos
