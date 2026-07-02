from typing import Any

from app.analyzers.base import Analyzer, DetectionResult
from app.models.post import Post


class LiveDetector(Analyzer):
    """Marca los posts que corresponden a un directo en curso, para disparar alerta inmediata."""

    name = "live_detector"

    async def analyze(self, post: Post, context: dict[str, Any] | None = None) -> DetectionResult | None:
        if not post.is_live or post.live_status != "LIVE":
            return None

        return DetectionResult(
            analyzer=self.name,
            result={"live_status": post.live_status, "permalink": post.permalink},
            score=1.0,
        )
