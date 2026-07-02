from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.keyword_rule import KeywordRule
from app.schemas.rule import KeywordRuleCreate, KeywordRuleRead, KeywordRuleUpdate

router = APIRouter()


@router.post("", response_model=KeywordRuleRead, status_code=201)
async def create_rule(payload: KeywordRuleCreate, db: AsyncSession = Depends(get_db)) -> KeywordRule:
    rule = KeywordRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("", response_model=list[KeywordRuleRead])
async def list_rules(db: AsyncSession = Depends(get_db)) -> list[KeywordRule]:
    result = await db.scalars(select(KeywordRule).order_by(KeywordRule.id.desc()))
    return list(result.all())


@router.patch("/{rule_id}", response_model=KeywordRuleRead)
async def update_rule(rule_id: int, payload: KeywordRuleUpdate, db: AsyncSession = Depends(get_db)) -> KeywordRule:
    rule = await db.get(KeywordRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    return rule
