from typing import Any

import httpx

from app.analyzers.base import Analyzer, DetectionResult
from app.core.config import settings
from app.models.post import Post

_PROMPT_TEMPLATE = (
    "Clasifica el sentimiento del siguiente texto en español respondiendo con "
    "EXACTAMENTE una palabra: positivo, negativo o neutro. No agregues explicaciones.\n\n"
    'Texto: "{text}"\n\nSentimiento:'
)

_SCORE_BY_LABEL = {"positivo": 1.0, "neutro": 0.0, "negativo": -1.0}


class SentimentAnalyzer(Analyzer):
    """Clasificación de sentimiento vía LLM local (Ollama)."""

    name = "sentiment"

    async def analyze(self, post: Post, context: dict[str, Any] | None = None) -> DetectionResult | None:
        text = (post.message or "").strip()
        if not text:
            return None

        prompt = _PROMPT_TEMPLATE.format(text=text[:2000])
        async with httpx.AsyncClient(base_url=settings.ollama_host, timeout=30.0) as client:
            response = await client.post(
                "/api/generate",
                json={"model": settings.ollama_llm_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip().lower()

        label = next((candidate for candidate in _SCORE_BY_LABEL if candidate in raw), "neutro")

        return DetectionResult(analyzer=self.name, result={"label": label, "raw": raw}, score=_SCORE_BY_LABEL[label])
