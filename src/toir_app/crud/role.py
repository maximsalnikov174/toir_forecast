from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Role, UserRole


async def get_superuser_role(session: AsyncSession) -> int:
    """Создание роли суперпользователя."""
    return await session.scalar(
        select(Role.id).where(Role.name == UserRole.ADMIN.value)
    )
