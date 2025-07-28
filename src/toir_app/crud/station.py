from http import HTTPStatus
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Station


async def get_multi(
    session: AsyncSession,
) -> Sequence[Station]:
    """Получение списка сервисных организаций."""
    stmt = select(Station).order_by(Station.name)
    result = await session.scalars(stmt)
    if not result:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Указанная работа не найдена.'
        )
    return result.all()
