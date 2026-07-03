"""Siembra datos de demostración para probar la plataforma SIN credenciales de Meta.

Crea una página ficticia (fb_page_id='DEMO_PAGE') con varios posts de temas
distintos, y los pasa por el bus de analizadores (sentimiento + embedding), de
modo que puedas ver el dashboard, las detecciones y la búsqueda semántica
funcionando de inmediato.

Uso (dentro del contenedor backend):
    python -m scripts.seed_demo          # inserta y analiza los posts demo
    python -m scripts.seed_demo --clean  # elimina todos los datos demo

NO usar en producción: es solo para pruebas locales.
"""

import sys

from sqlalchemy import delete, select

from app.db.sync_session import SyncSessionLocal
from app.models.detection import Detection
from app.models.embedding import PostEmbedding
from app.models.image_embedding import PostImageEmbedding
from app.models.page import Page
from app.models.post import Post
from app.workers.tasks import process_post

DEMO_FB_PAGE_ID = "DEMO_PAGE"

# (platform_post_id, mensaje, [urls de imágenes])
DEMO_POSTS = [
    ("demo_post_1", "La Municipalidad de Trujillo anunció la construcción de una nueva carretera hacia Laredo.", []),
    ("demo_post_2", "La ONPE informó los resultados oficiales de las elecciones generales en Lima y Arequipa.", []),
    ("demo_post_3", "El Ministerio de Salud y el hospital Loayza alertan por el aumento de casos de dengue en Piura.", []),
    ("demo_post_4", "Vecinos de San Juan de Lurigancho protestan por los cortes de agua de Sedapal.", []),
    # Posts con imágenes reales para probar la búsqueda visual (fuentes que permiten hotlinking):
    (
        "demo_img_dog",
        "Nuestra mascota del refugio busca un hogar.",
        ["https://picsum.photos/id/237/640/480"],
    ),
    (
        "demo_img_soccer",
        "Así se vivió el partido de fútbol este fin de semana.",
        ["https://ultralytics.com/images/zidane.jpg"],
    ),
    (
        "demo_img_bus",
        "Reporte de tránsito: precaución con el transporte público en la vía.",
        ["https://ultralytics.com/images/bus.jpg"],
    ),
]


def clean() -> None:
    with SyncSessionLocal() as db:
        page = db.scalar(select(Page).where(Page.fb_page_id == DEMO_FB_PAGE_ID))
        if page is None:
            print("No hay datos demo que borrar.")
            return

        post_ids = list(db.scalars(select(Post.id).where(Post.page_id == page.id)))
        if post_ids:
            db.execute(delete(PostEmbedding).where(PostEmbedding.post_id.in_(post_ids)))
            db.execute(delete(PostImageEmbedding).where(PostImageEmbedding.post_id.in_(post_ids)))
            db.execute(delete(Detection).where(Detection.post_id.in_(post_ids)))
            db.execute(delete(Post).where(Post.id.in_(post_ids)))
        db.delete(page)
        db.commit()
        print(f"Borrados: página demo + {len(post_ids)} posts.")


def seed() -> None:
    new_ids: list[int] = []
    with SyncSessionLocal() as db:
        page = db.scalar(select(Page).where(Page.fb_page_id == DEMO_FB_PAGE_ID))
        if page is None:
            page = Page(
                fb_page_id=DEMO_FB_PAGE_ID,
                name="Página demo (seed)",
                category="News & Media",
                is_active=True,
            )
            db.add(page)
            db.commit()
            db.refresh(page)

        for platform_post_id, message, media_urls in DEMO_POSTS:
            if db.scalar(select(Post.id).where(Post.platform_post_id == platform_post_id)):
                continue
            post = Post(
                page_id=page.id,
                platform_post_id=platform_post_id,
                type="photo" if media_urls else "status",
                message=message,
                media_urls=media_urls or None,
            )
            db.add(post)
            db.commit()
            db.refresh(post)
            new_ids.append(post.id)

        print(f"Insertados {len(new_ids)} posts demo en la página '{page.name}' (id={page.id}).")

    for post_id in new_ids:
        process_post(post_id)
        print(f"  analizado post {post_id} (sentimiento + embedding + imágenes)")

    print("Listo.")
    print("  Búsqueda de texto:   http://localhost:8000/api/search?q=epidemias")
    print("  Búsqueda visual:     http://localhost:8000/api/search/images?q=perro")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        seed()
