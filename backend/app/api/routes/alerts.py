from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertRead

router = APIRouter()


@router.get("", response_model=list[AlertRead])
async def list_alerts(db: AsyncSession = Depends(get_db)) -> list[Alert]:
    result = await db.scalars(select(Alert).order_by(Alert.sent_at.desc()))
    return list(result.all())
