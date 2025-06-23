from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.stats import add_statement_after_loading_csv_file

router = APIRouter()


@router.get(
    '/fix_stats',
    name='Фиксация статистики'
)
async def fix_stats(session: AsyncSession = Depends(get_async_session)):
    await add_statement_after_loading_csv_file(session=session)
