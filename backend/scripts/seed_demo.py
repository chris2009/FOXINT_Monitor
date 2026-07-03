"""Siembra datos de demostración para probar la plataforma SIN credenciales de Meta/YouTube.

Crea objetivos ficticios (una Página de Facebook y un canal de YouTube) con varios
posts/videos, y los pasa por el bus de analizadores, de modo que puedas ver el dashboard,
las detecciones y las búsquedas (texto, visual, facial, entidades) funcionando de inmediato.

Uso (dentro del contenedor backend):
    python -m scripts.seed_demo          # inserta y analiza los datos demo
    python -m scripts.seed_demo --clean  # elimina todos los datos demo

NO usar en producción: es solo para pruebas locales.
"""

import sys

from sqlalchemy import delete, select

from app.db.sync_session import SyncSessionLocal
from app.models.detection import Detection
from app.models.embedding import PostEmbedding
from app.models.face import PostFace
from app.models.image_embedding import PostImageEmbedding
from app.models.page import Page
from app.models.post import Post
from app.workers.tasks import process_post

# Cada objetivo demo: (external_id, nombre, categoría, plataforma, [posts]).
# Cada post: (platform_post_id, mensaje, [urls de imágenes/miniaturas], type).
DEMO_TARGETS = [
    {
        "external_id": "DEMO_PAGE",
        "name": "Página demo (seed)",
        "category": "News & Media",
        "platform": "facebook",
        "posts": [
            ("demo_post_1", "La Municipalidad de Trujillo anunció la construcción de una nueva carretera hacia Laredo.", [], "status"),
            ("demo_post_2", "La ONPE informó los resultados oficiales de las elecciones generales en Lima y Arequipa.", [], "status"),
            ("demo_post_3", "El Ministerio de Salud y el hospital Loayza alertan por el aumento de casos de dengue en Piura.", [], "status"),
            ("demo_post_4", "Vecinos de San Juan de Lurigancho protestan por los cortes de agua de Sedapal.", [], "status"),
            ("demo_img_dog", "Nuestra mascota del refugio busca un hogar.", ["https://picsum.photos/id/237/640/480"], "photo"),
            ("demo_img_soccer", "Así se vivió el partido de fútbol este fin de semana.", ["https://ultralytics.com/images/zidane.jpg"], "photo"),
            ("demo_img_bus", "Reporte de tránsito: precaución con el transporte público en la vía.", ["https://ultralytics.com/images/bus.jpg"], "photo"),
            # Post con audio para probar la transcripción (Whisper); Whisper detecta el idioma solo.
            ("demo_audio", "Audio de prueba para transcripción automática.", ["https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"], "video"),
        ],
    },
    {
        "external_id": "DEMO_YT_CHANNEL",
        "name": "Canal demo YouTube (seed)",
        "category": "YouTube Channel",
        "platform": "youtube",
        "posts": [
            ("demo_yt_1", "ONPE: cómo votar en las elecciones\n\nGuía de la ONPE para el proceso electoral en Lima.", ["https://picsum.photos/id/1015/640/480"], "video"),
            ("demo_yt_2", "Reporte de tránsito en Trujillo\n\nEstado de las vías y el transporte público hoy.", ["https://ultralytics.com/images/bus.jpg"], "video"),
        ],
    },
]

_ALL_EXTERNAL_IDS = [t["external_id"] for t in DEMO_TARGETS]


def clean() -> None:
    with SyncSessionLocal() as db:
        pages = list(db.scalars(select(Page).where(Page.fb_page_id.in_(_ALL_EXTERNAL_IDS))))
        if not pages:
            print("No hay datos demo que borrar.")
            return

        page_ids = [p.id for p in pages]
        post_ids = list(db.scalars(select(Post.id).where(Post.page_id.in_(page_ids))))
        if post_ids:
            db.execute(delete(PostEmbedding).where(PostEmbedding.post_id.in_(post_ids)))
            db.execute(delete(PostImageEmbedding).where(PostImageEmbedding.post_id.in_(post_ids)))
            db.execute(delete(PostFace).where(PostFace.post_id.in_(post_ids)))
            db.execute(delete(Detection).where(Detection.post_id.in_(post_ids)))
            db.execute(delete(Post).where(Post.id.in_(post_ids)))
        db.execute(delete(Page).where(Page.id.in_(page_ids)))
        db.commit()
        print(f"Borrados: {len(pages)} objetivos demo + {len(post_ids)} posts.")


def seed() -> None:
    new_ids: list[int] = []
    with SyncSessionLocal() as db:
        for target in DEMO_TARGETS:
            page = db.scalar(select(Page).where(Page.fb_page_id == target["external_id"]))
            if page is None:
                page = Page(
                    fb_page_id=target["external_id"],
                    name=target["name"],
                    category=target["category"],
                    platform=target["platform"],
                    is_active=True,
                )
                db.add(page)
                db.commit()
                db.refresh(page)

            for platform_post_id, message, media_urls, post_type in target["posts"]:
                if db.scalar(select(Post.id).where(Post.platform_post_id == platform_post_id)):
                    continue
                permalink = (
                    f"https://www.youtube.com/watch?v={platform_post_id}"
                    if target["platform"] == "youtube"
                    else None
                )
                post = Post(
                    page_id=page.id,
                    platform_post_id=platform_post_id,
                    type=post_type,
                    message=message,
                    permalink=permalink,
                    media_urls=media_urls or None,
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                new_ids.append(post.id)

            print(f"Objetivo '{page.name}' ({page.platform}) listo (id={page.id}).")

    for post_id in new_ids:
        process_post(post_id)
        print(f"  analizado post {post_id}")

    print("Listo.")
    print("  Búsqueda de texto:  http://localhost:8000/api/search?q=elecciones")
    print("  Búsqueda visual:    http://localhost:8000/api/search/images?q=un%20autobus")
    print("  Entidades:          http://localhost:8000/api/entities")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        seed()
