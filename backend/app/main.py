from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    alerts,
    entities,
    face_search,
    image_search,
    pages,
    posts,
    rules,
    search,
)
from app.core.config import settings

app = FastAPI(title="OSINT Monitor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pages.router, prefix="/api/pages", tags=["pages"])
app.include_router(posts.router, prefix="/api")
app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(image_search.router, prefix="/api/search/images", tags=["search"])
app.include_router(face_search.router, prefix="/api/search/faces", tags=["search"])
app.include_router(entities.router, prefix="/api/entities", tags=["entities"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
