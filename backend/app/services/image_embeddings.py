"""Embeddings de imagen con CLIP (búsqueda visual local, vía sentence-transformers).

CLIP proyecta imágenes y texto al MISMO espacio vectorial (512d), lo que habilita:
  - texto -> imagen: buscar fotos por una descripción ("multitud", "incendio").
  - imagen -> imagen: subir una foto y encontrar imágenes visualmente similares.

Se usan dos modelos que comparten el espacio:
  - clip-ViT-B-32                 -> encoder de imágenes.
  - clip-ViT-B-32-multilingual-v1 -> encoder de texto multilingüe (español incl.),
                                     alineado al espacio de imágenes de CLIP.

Los modelos se cargan de forma perezosa y se cachean por proceso (son costosos en RAM;
por eso el worker corre con baja concurrencia). Las funciones son SÍNCRONAS: en el worker
(Celery) se llaman directo; en la API (FastAPI) se envuelven en un threadpool.
"""

import io
from functools import lru_cache
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

IMAGE_EMBEDDING_DIM = 512

_IMAGE_MODEL_NAME = "clip-ViT-B-32"
_TEXT_MODEL_NAME = "clip-ViT-B-32-multilingual-v1"


@lru_cache(maxsize=1)
def _image_model() -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_IMAGE_MODEL_NAME)


@lru_cache(maxsize=1)
def _text_model() -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_TEXT_MODEL_NAME)


def embed_image(image_bytes: bytes) -> list[float]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    vector = _image_model().encode(image, normalize_embeddings=True)
    return vector.tolist()


def embed_text_clip(text: str) -> list[float]:
    vector = _text_model().encode(text, normalize_embeddings=True)
    return vector.tolist()
