"""App Celery: worker (bus de analizadores) + beat (scheduler de polling por página).

`dispatch_due_pages` corre cada 60s y decide, por página, si ya se cumplió su
`poll_interval` individual (ver app/workers/tasks.py) — así cada página respeta su
propio intervalo configurado sin necesitar una entrada de beat por página.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "osint_monitor",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "dispatch-due-pages": {
            "task": "osint.dispatch_due_pages",
            "schedule": 60.0,
        },
    },
)

# Import al final: registra las tareas en `celery_app` (tasks.py importa `celery_app` desde este
# mismo módulo, que ya existe en sys.modules con el atributo definido para ese momento).
from app.workers import tasks  # noqa: E402,F401
