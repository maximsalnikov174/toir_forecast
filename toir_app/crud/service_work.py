from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.crud.car import get_car_by_pk
from toir_app.crud.service_status import get_multi_service_status
from toir_app.models import ServiceWork
from toir_app.models.car import Car
from toir_app.schemas.service_work import CarAtributesInServiceWork


async def get_service_work(
        service_work_id: int,
        session: AsyncSession
) -> Optional[ServiceWork]:
    """Получение объекта модели ServiceWork по ID."""
    return await session.get(ServiceWork, service_work_id)


async def get_last_service_with_current_service_id(
        car_id: int,
        last_service_id: int,
        session: AsyncSession
):
    """
    Возвращает последнюю (свежую) запись сервисного обслуживания.

    Args:
        - car_id : ID выбранного ТС
        - last_service_id : ID вида обслуживания, для которого выполняется поиск

    Returns:
        - оbj(ServiceWork)
    """
    return await session.scalar(
        select(ServiceWork).where(
            ServiceWork.car_id == car_id,
            ServiceWork.last_service_id == last_service_id,
        ).order_by(
            ServiceWork.last_service_reading.desc()
        ).limit(1)
    )


async def get_last_request_reading_by_car(
        car_id: int,
        session: AsyncSession
):
    """Для передачи данных о машине (общий и суточный пробеги)."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.car_id == car_id)
        .order_by(ServiceWork.request_date.desc())
        .limit(1)
    )
    return CarAtributesInServiceWork.model_validate(result)


async def check_zvr_unique(
        zvr_number: int,
        session: AsyncSession
) -> bool:
    """Проверяет ЗВР на уникальный номер."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.zvr_number == zvr_number)
    )
    return True if result else False


async def get_active_service_work_list_by_car(
        car_id: int,
        request_status_id: int,
        session: AsyncSession
) -> list[ServiceWork]:
    """Получение списка (неархивных) сервисных обслуживаний для ТС.

    Filters:
        - для всех расчётных статусов, строже выбранного.

    Order_by:
        - по возрастанию ID service_name (идентично шапке в итоговой таблице).
    """
    await get_car_by_pk(car_id, session)

    result = await session.scalars(
        select(ServiceWork)
        .where(
            ServiceWork.car_id == car_id,
            ServiceWork.request_status_id <= request_status_id,
            ServiceWork.in_archive.is_(False)
        )
        .order_by(
            ServiceWork.next_service_id  # сортировка по ID вида работ
        )
    )

    return result.all()


async def _get_active_service_work_with_service_status(
        *,
        organization_id: int,
        service_status_id: int,
        session: AsyncSession
):
    """Получение активных сервисных работ с расчётным статусом."""
    result = await session.scalars(
        select(ServiceWork)
        .join(Car)
        .where(
            Car.organization_id == organization_id,
            ServiceWork.request_status_id == service_status_id,
            ServiceWork.in_archive.is_(False)
        )
    )
    return result.all()


async def get_active_service_work_count_for_all_service_status(
        organization_id: int,
        session: AsyncSession
) -> dict[str, int]:
    """Получение сводных данных о количестве активных работ по статусам."""
    # Получение списка сервисных статусов:
    service_statuses = await get_multi_service_status(session=session)

    # Подготовка пустого словаря:
    summary_data = {}

    # Перебор и наполнение:
    for service_status in service_statuses:
        value = await _get_active_service_work_with_service_status(
            organization_id=organization_id,
            service_status_id=service_status.id,
            session=session
        )
        summary_data[service_status.name] = len(value)

    return summary_data


async def get_all_active_service_work_with_open_zvr(
        organization_id: int,
        session: AsyncSession
):
    """Получение «зависших» активных сервисных работ."""
    result = await session.scalars(
        select(ServiceWork)
        .join(Car)
        .where(
            Car.organization_id == organization_id,
            ServiceWork.service_work_completed.is_(True),
            ServiceWork.in_archive.is_(False)
        )
    )
    return result.all()
