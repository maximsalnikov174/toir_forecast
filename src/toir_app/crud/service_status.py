from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import DAOBase
from exception import ObjectIsExistException
from models import ServiceStatus


class DAOServiceStatus(DAOBase):
    """CRUD-класс для ServiceStatus."""

    async def check_name_duplicate(
            self, value: str, session: AsyncSession
    ) -> None:
        """Проверка расчётного статуса на дублирование имени."""
        obj = await self.get_by_attribute('name', value, session)

        # Выбрасываем исключение, если существует:
        if obj:
            raise ObjectIsExistException

    async def check_exists(self, id: int, session: AsyncSession):
        """Проверка существования расчётного статуса по его ID."""
        if not await self.get(obj_id=id, session=session):
            raise HTTPException(
                status_code=404,
                detail=(
                    'Экземпляр ServiceStatus с параметром '
                    f'{id} в БД не найден.'
                )
            )


dao_service_status = DAOServiceStatus(ServiceStatus)
