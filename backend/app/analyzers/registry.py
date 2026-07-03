from app.analyzers.base import Analyzer
from app.analyzers.keyword import KeywordAnalyzer
from app.analyzers.live_detector import LiveDetector
from app.analyzers.ner import NERAnalyzer
from app.analyzers.sentiment import SentimentAnalyzer


def get_analyzers() -> list[Analyzer]:
    """Registro del bus de analizadores activos. Agregar uno nuevo = instanciarlo aquí."""
    return [KeywordAnalyzer(), SentimentAnalyzer(), NERAnalyzer(), LiveDetector()]
