"""Detección y embedding de caras (facenet-pytorch), para búsqueda por SIMILITUD facial.

Alcance (importante): esto sirve para encontrar imágenes con caras parecidas DENTRO del
corpus que el sistema ya capturó de páginas públicas autorizadas. NO identifica ni nombra
personas, NO hace reconocimiento biométrico de identidad, y NO busca en la web abierta
(ver PROYECTO_OSINT_MONITOR.md, secciones 1.2.12 y 10.6).

MTCNN detecta y recorta caras; InceptionResnetV1 (VGGFace2) las convierte en un vector de
512d ya normalizado (apto para distancia coseno). Modelos cargados de forma perezosa por
proceso; por eso el worker corre con baja concurrencia.
"""

import io
from functools import lru_cache
from typing import Any, TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from facenet_pytorch import MTCNN, InceptionResnetV1

FACE_EMBEDDING_DIM = 512


@lru_cache(maxsize=1)
def _detector() -> "MTCNN":
    from facenet_pytorch import MTCNN

    # keep_all=True -> detecta TODAS las caras de la imagen (un post puede tener varias).
    return MTCNN(keep_all=True, post_process=True)


@lru_cache(maxsize=1)
def _encoder() -> "InceptionResnetV1":
    from facenet_pytorch import InceptionResnetV1

    return InceptionResnetV1(pretrained="vggface2").eval()


def _open_rgb(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def index_faces(image_bytes: bytes) -> list[dict[str, Any]]:
    """Devuelve una lista con {bbox, embedding} por cada cara detectada en la imagen."""
    import torch

    image = _open_rgb(image_bytes)
    boxes, _probs = _detector().detect(image)
    faces = _detector()(image)  # tensor [n, 3, 160, 160] o None
    if faces is None or boxes is None:
        return []

    with torch.no_grad():
        embeddings = _encoder()(faces)  # [n, 512], ya normalizados

    results: list[dict[str, Any]] = []
    for index, (box, embedding) in enumerate(zip(boxes, embeddings)):
        results.append(
            {
                "bbox": [float(v) for v in box.tolist()],
                "embedding": embedding.tolist(),
                "face_index": index,
            }
        )
    return results


def embed_face(image_bytes: bytes) -> list[float] | None:
    """Embedding de la cara más prominente de una imagen (para la consulta). None si no hay cara."""
    import torch

    image = _open_rgb(image_bytes)
    boxes, probs = _detector().detect(image)
    faces = _detector()(image)
    if faces is None or boxes is None or len(faces) == 0:
        return None

    # Elegir la cara con mayor confianza.
    best = max(range(len(faces)), key=lambda i: (probs[i] if probs is not None else 0.0))
    with torch.no_grad():
        embedding = _encoder()(faces[best].unsqueeze(0))[0]
    return embedding.tolist()
