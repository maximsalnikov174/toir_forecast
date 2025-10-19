from datetime import date, timedelta
from http import HTTPStatus
from typing import Annotated, Optional, Union

from fastapi import HTTPException
from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from api.endpoints.bot import bot_schedular
from crud.base import DAOBase
from exception import NotFoundError
from logger.logger import logger
from models import (
    EventForBot,
    Role,
    SpecialStatus,
    SpecialStatusForCar,
    special_status_role_association
)


class DAOSpecialStatusForCar(DAOBase[SpecialStatusForCar]):
    """DAO для работы с моделью специальных статусов для ТС."""

    model = SpecialStatusForCar

    async def get(self, obj_id, session):
        """Получение специальных статусов для ТС, расширенное доп.полями."""
        return await session.scalar(
            select(self.model)
            .options(
                joinedload(self.model.car),
                joinedload(self.model.special_status)
            ).where(self.model.id == obj_id)
        )


dao_special_status_for_car = DAOSpecialStatusForCar(SpecialStatusForCar)


async def get_all_special_status(
        session: AsyncSession,
        role_id: Optional[Annotated[int, Role.id]] = None,
):
    """Получение списка спец.статусов, доступных конкретному пользователю."""
    query = (
        select(SpecialStatus)
    )
    if role_id:
        query = (
            query.join(SpecialStatus.allowed_roles)
            .options(selectinload(SpecialStatus.allowed_roles))
            .where(Role.id == role_id)
        )

    result = await session.scalars(query)
    return result.all()


async def deactivate_special_status_for_car(
        special_status_for_car: SpecialStatusForCar,
        session: AsyncSession
) -> None:
    """Деактивирует специальный статус для карточки (без commit)."""
    special_status_for_car.is_active = False
    session.add(special_status_for_car)


async def get_special_status_for_car_list_where_left_yesterday(
        session: AsyncSession
) -> ScalarResult[SpecialStatusForCar]:
    """Получение карточек специальных статусов с истекшим сроком действия."""
    return await session.scalars(
        select(SpecialStatusForCar)
        .options(
            joinedload(SpecialStatusForCar.car),
            joinedload(SpecialStatusForCar.special_status)
        ).where(
            SpecialStatusForCar.date_left <= date.today() - timedelta(1),
            SpecialStatusForCar.is_active.is_(True)
        )
    )


async def deactivate_list_of_special_status_for_car(
        session: AsyncSession
) -> None:
    """Деактивирует список карточек специальных статусов для ТС.

    ## Detail:
    - Карточки имеют истекший срок действия.
    - Выполняется commit внутри функции.
    """
    cards = (await get_special_status_for_car_list_where_left_yesterday(
        session)).all()
    for card in cards:
        await deactivate_special_status_for_car(
            special_status_for_car=card,
            session=session
        )

        # Отправка сообщения в телегу о закрытии статуса ТС:
        await bot_schedular.send_notification(
            obj=card,
            event=EventForBot.END_FOR_STATUS
        )

        logger.info(
            f'Закрыт статус «{card.special_status.name}» для «{card.car.grz}».'
        )

    await session.commit()


async def get_special_status_by_id(
        special_status_id: Annotated[int, SpecialStatus.id],
        session: AsyncSession,
        expand_data: bool = False,
) -> Optional[SpecialStatus]:
    """
    Получает специальный статус по ID с опциональной загрузкой связанных ролей.

    Args:
        service_status_id: ID специального статуса
        session: Асинхронная сессия SQLAlchemy
        expand_data: Флаг для загрузки связанных ролей

    Returns:
        Объект SpecialStatus или None, если не найден
    """
    query = select(SpecialStatus).where(SpecialStatus.id == special_status_id)

    if expand_data:
        query = query.options(selectinload(SpecialStatus.allowed_roles))

    result = await session.scalar(query)

    if not result:
        raise NotFoundError(
            reason=f'Специальный статус {special_status_id} не найден.'
        )

    return result


async def check_special_status_exists(
        query: Union[int, list[int]],
        session: AsyncSession
) -> bool:
    """Проверяет существование специальных статусов."""
    if isinstance(query, list):
        for value in query:
            await get_special_status_by_id(value, session)
    else:
        await get_special_status_by_id(query, session)

    return True


async def association_special_status_and_role(
        special_status_id: Annotated[int, SpecialStatus.id],
        role_id: Annotated[int, Role.id],
        session: AsyncSession,
):
    """Добавление ID специального статуса и ID роли в таблицу."""
    stmt = special_status_role_association.insert().values(
            special_status_id=special_status_id,
            role_id=role_id
        )
    await session.execute(stmt)
    await session.commit()


async def create_association_special_statuses_and_role(
        special_status_ids: list[Annotated[int, SpecialStatus.id]],
        role_id: Annotated[int, Role.id],
        session: AsyncSession,
) -> bool:
    try:
        await check_special_status_exists(special_status_ids, session)

        # Проверяем существование роли:
        # TODO await check_role_exist(role_id, session) по аналогии ^

        # Проверяем существование связей (если добавлены ранее):
        # TODO

        for special_status_id in special_status_ids:
            await association_special_status_and_role(
                special_status_id=special_status_id,
                role_id=role_id,
                session=session
            )

        return True  # Либо всё записывается, либо ничего

    except NotFoundError as e:
        raise HTTPException(
            HTTPStatus.NO_CONTENT,
            detail=f'Не найдены данные: {e.reason}',
        )

    except Exception as e:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f'Прочая проблема: {e}',
        )
