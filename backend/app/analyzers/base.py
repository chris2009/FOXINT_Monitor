"""Contrato del bus de analizadores (réplica del "bus de analíticas agnóstico" de Intelion).

Cada analizador es un plugin intercambiable: recibe un Post y opcionalmente contexto
(ej. reglas de keywords activas), y devuelve un DetectionResult o None si no aplica
(por ejemplo, un post sin texto no genera detección de sentimiento).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.models.post import Post


@dataclass
class DetectionResult:
    analyzer: str
    result: dict[str, Any]
    score: float | None = None


class Analyzer(ABC):
    name: str

    @abstractmethod
    async def analyze(self, post: Post, context: dict[str, Any] | None = None) -> DetectionResult | None: ...
