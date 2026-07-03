"""Generación de embeddings de texto vía Ollama (nomic-embed-text).

Se reutiliza en dos lugares:
  - al indexar cada post nuevo (process_post) -> se guarda en post_embeddings.
  - al buscar (endpoint /api/search) -> se embebe la consulta del usuario.

nomic-embed-text usa prefijos de tarea: los documentos se embeben con
"search_document: " y las consultas con "search_query: ". Usar el prefijo
correcto en cada lado mejora la calidad del ranking por similitud.
"""

import httpx

from app.core.config import settings

EMBEDDING_DIM = 768  # nomic-embed-text


async def embed_text(content: str, *, is_query: bool = False) -> list[float]:
    prefix = "search_query: " if is_query else "search_document: "
    async with httpx.AsyncClient(base_url=settings.ollama_host, timeout=30.0) as client:
        response = await client.post(
            "/api/embeddings",
            json={"model": settings.ollama_embed_model, "prompt": prefix + content},
        )
        response.raise_for_status()
        return response.json()["embedding"]
