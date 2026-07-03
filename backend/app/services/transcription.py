"""Transcripción de audio/video con faster-whisper (Speech-to-Text local).

Convierte el audio hablado de un archivo (mp3/wav/mp4/webm/…) en texto buscable. El
decodificado lo hace la librería `av` (PyAV, con ffmpeg embebido), así que no hace falta
ffmpeg del sistema. El modelo se descarga en el primer uso a un volumen (whispercache).

El motor es genérico: transcribe cualquier media que el sistema pueda descargar. La fuente
del audio (post de video de Facebook, archivo subido, etc.) es responsabilidad del llamador.
"""

import tempfile
from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

# Extensiones que consideramos audio/video transcribible.
AUDIO_VIDEO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".mp4", ".webm", ".mov", ".mkv")


@lru_cache(maxsize=1)
def _model() -> "WhisperModel":
    from faster_whisper import WhisperModel

    return WhisperModel(
        settings.whisper_model,
        device="cpu",
        compute_type=settings.whisper_compute,
        download_root=settings.whisper_cache_dir,
    )


def is_transcribable_url(url: str) -> bool:
    lowered = url.lower().split("?")[0]
    return lowered.endswith(AUDIO_VIDEO_EXTENSIONS)


def transcribe_media(media_bytes: bytes) -> tuple[str, str | None]:
    """Transcribe los bytes de un archivo de audio/video. Devuelve (texto, idioma_detectado)."""
    with tempfile.NamedTemporaryFile(suffix=".media") as tmp:
        tmp.write(media_bytes)
        tmp.flush()
        segments, info = _model().transcribe(tmp.name, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments).strip()
    language = getattr(info, "language", None)
    return text, language
