"""Cliente async para la Graph API de Meta.

Contiene la validación crítica del proyecto (ver PROYECTO_OSINT_MONITOR.md, sección 2):
el sistema SOLO monitorea Páginas públicas, nunca perfiles personales. La regla técnica
es simple: una Página expone el campo `category` en `/{id}?fields=...,category`; un
perfil personal no lo expone (o la llamada falla por permisos). `validate_is_page` es
el punto de entrada obligatorio antes de registrar cualquier objetivo nuevo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.services.graph_api.exceptions import GraphAPIError, NotAPageError, RateLimitedError

GRAPH_API_BASE_URL = "https://graph.facebook.com"

# Códigos de error de Meta asociados a rate limiting / throttling de la app.
# Ref: https://developers.facebook.com/docs/graph-api/guides/error-handling
_RATE_LIMIT_ERROR_CODES = {4, 17, 32, 613}


@dataclass(frozen=True)
class PageInfo:
    """Metadatos de una Página pública, ya validada."""

    id: str
    name: str
    category: str
    fan_count: int | None = None
    followers_count: int | None = None


class GraphAPIClient:
    """Cliente delgado sobre la Graph API. Una instancia por request/tarea (async context manager)."""

    def __init__(
        self,
        access_token: str | None = None,
        api_version: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._access_token = access_token or settings.fb_access_token
        self._api_version = api_version or settings.graph_api_version
        self._base_url = f"{GRAPH_API_BASE_URL}/{self._api_version}"
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def __aenter__(self) -> "GraphAPIClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"access_token": self._access_token, **(params or {})}
        response = await self._client.get(path, params=query)
        payload = response.json()

        if "error" in payload:
            error = payload["error"]
            code = error.get("code")
            message = error.get("message", "Graph API error desconocido")
            if code in _RATE_LIMIT_ERROR_CODES:
                raise RateLimitedError(f"Rate limit de Graph API (code={code}): {message}")
            raise GraphAPIError(f"Graph API error (code={code}): {message}")

        return payload

    async def get_target_metadata(self, target_id: str) -> dict[str, Any]:
        """Consulta cruda de `/{id}?fields=id,name,category,fan_count,followers_count`.

        No lanza NotAPageError: devuelve el payload tal cual para que el llamador
        decida (usado internamente por `validate_is_page`).
        """
        fields = "id,name,category,fan_count,followers_count"
        return await self._get(f"/{target_id}", {"fields": fields})

    async def validate_is_page(self, target_id: str) -> PageInfo:
        """Valida que `target_id` sea una Página pública. Lanza NotAPageError si es un perfil.

        Regla (documento sección 2.2): si la respuesta trae `category`, es una Página
        (se puede "seguir"). Si no trae `category` -o la llamada falla por permisos-,
        es un perfil personal y queda fuera de alcance del sistema.
        """
        try:
            data = await self.get_target_metadata(target_id)
        except GraphAPIError as exc:
            raise NotAPageError(
                f"No se pudo validar '{target_id}' como Página (posible perfil personal o ID inválido): {exc}"
            ) from exc

        category = data.get("category")
        if not category:
            raise NotAPageError(
                f"'{target_id}' no expone 'category' → es un perfil personal, fuera de alcance del sistema."
            )

        return PageInfo(
            id=data["id"],
            name=data.get("name", ""),
            category=category,
            fan_count=data.get("fan_count"),
            followers_count=data.get("followers_count"),
        )

    async def get_posts(self, page_id: str, limit: int = 25, since: str | None = None) -> list[dict[str, Any]]:
        """Publicaciones recientes de la página (`/{page-id}/posts`)."""
        fields = "id,message,permalink_url,created_time,attachments{media_type,url,media}"
        params: dict[str, Any] = {"fields": fields, "limit": limit}
        if since:
            params["since"] = since
        data = await self._get(f"/{page_id}/posts", params)
        return data.get("data", [])

    async def get_live_videos(self, page_id: str) -> list[dict[str, Any]]:
        """Directos de la página, en curso o finalizados (`/{page-id}/live_videos`).

        `status` puede ser LIVE o VOD; permite detectar un live iniciado en el mismo poll.
        """
        fields = "id,status,permalink_url,creation_time,title"
        data = await self._get(f"/{page_id}/live_videos", {"fields": fields})
        return data.get("data", [])
