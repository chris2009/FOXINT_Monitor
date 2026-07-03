"""Analizador de entidades nombradas (NER) con spaCy en español.

Extrae del texto del post las personas, lugares y organizaciones mencionadas
(lo que en INTELION es el panel "Entidades"). El resultado se guarda como una
detección con analyzer="ner" y luego se agrega en /api/entities.
"""

from functools import lru_cache
from typing import Any, TYPE_CHECKING

from app.analyzers.base import Analyzer, DetectionResult
from app.models.post import Post

if TYPE_CHECKING:
    from spacy.language import Language

_SPACY_MODEL = "es_core_news_md"

# Etiquetas de spaCy (modelo español) -> tipo legible en la UI.
_LABEL_MAP = {
    "PER": "persona",
    "LOC": "lugar",
    "ORG": "organización",
    "MISC": "otro",
}


@lru_cache(maxsize=1)
def _nlp() -> "Language":
    import spacy

    # Solo se necesita el componente NER; se desactiva el resto para ir más rápido.
    return spacy.load(_SPACY_MODEL, disable=["lemmatizer", "attribute_ruler", "morphologizer"])


class NERAnalyzer(Analyzer):
    name = "ner"

    async def analyze(self, post: Post, context: dict[str, Any] | None = None) -> DetectionResult | None:
        text = (post.message or "").strip()
        if not text:
            return None

        doc = _nlp()(text[:5000])

        seen: set[tuple[str, str]] = set()
        entities: list[dict[str, str]] = []
        for ent in doc.ents:
            entity_type = _LABEL_MAP.get(ent.label_, "otro")
            key = (ent.text.strip().lower(), entity_type)
            if not ent.text.strip() or key in seen:
                continue
            seen.add(key)
            entities.append({"text": ent.text.strip(), "type": entity_type})

        if not entities:
            return None

        return DetectionResult(analyzer=self.name, result={"entities": entities}, score=float(len(entities)))
