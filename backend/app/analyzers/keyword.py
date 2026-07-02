from typing import Any

from app.analyzers.base import Analyzer, DetectionResult
from app.models.keyword_rule import KeywordRule
from app.models.post import Post


class KeywordAnalyzer(Analyzer):
    """Matching de `post.message` contra las `keyword_rules` activas."""

    name = "keyword"

    async def analyze(self, post: Post, context: dict[str, Any] | None = None) -> DetectionResult | None:
        text = (post.message or "").lower()
        if not text:
            return None

        rules: list[KeywordRule] = (context or {}).get("keyword_rules", [])
        matches: list[dict[str, Any]] = []

        for rule in rules:
            keywords = [kw.lower() for kw in rule.keywords]
            hits = [kw for kw in keywords if kw in text]
            if not hits:
                continue
            if rule.match_type == "all" and len(hits) != len(keywords):
                continue
            if rule.match_type == "phrase" and " ".join(keywords) not in text:
                continue
            matches.append({"rule_id": rule.id, "label": rule.label, "severity": rule.severity, "hits": hits})

        if not matches:
            return None

        return DetectionResult(analyzer=self.name, result={"matches": matches}, score=float(len(matches)))
