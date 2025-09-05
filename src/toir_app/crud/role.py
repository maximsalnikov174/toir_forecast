from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import DAOBase
from models import Role, UserRole


class DAORole(DAOBase[Role]):
    """DAO для работы с моделью роли."""

    model = Role


dao_role = DAORole(Role)


async def get_superuser_role(session: AsyncSession) -> int:
    """Создание роли суперпользователя."""
    return await session.scalar(
        select(Role.id).where(Role.name == UserRole.ADMIN.value)
    )
