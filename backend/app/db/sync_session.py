"""Sesión síncrona de SQLAlchemy, usada por las tareas de Celery.

FastAPI usa el engine async (`session.py`) porque corre en un loop de asyncio propio.
Celery, en cambio, ejecuta tareas en hilos/procesos síncronos, por lo que aquí usamos
un engine síncrono (psycopg2) en vez de mezclar asyncio dentro de las tareas.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(_sync_database_url, echo=settings.environment == "development")

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
