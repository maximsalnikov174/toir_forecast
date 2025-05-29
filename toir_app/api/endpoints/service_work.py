from datetime import datetime as dt
# from datetime import tzinfo
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

# from toir_app.constants import TIMEZONE_AE
from toir_app.core.db import get_async_session
from toir_app.crud.service_work import (
    check_zvr_unique,
    create_main_table,
    get_active_service_work_count_for_all_service_status,
    get_all_active_service_work_with_open_zvr,
    get_service_work,
    get_active_service_work_list_by_car,
)
from toir_app.schemas.service_work import (
    ServiceWorkWithZVRNumber
)

router = APIRouter()


@router.patch(
    '/add_zvr',
    response_model=ServiceWorkWithZVRNumber,
    name='Добавление ЗВР к конкретному service_work',
    description=(
        '* если ЗВР создан - автоматически фиксируется дата создания\n'
        '* создать ЗВР повторно НЕЛЬЗЯ\n'
        '* ЗВР - всегда уникальное 7-значное число'
    ),
    response_model_exclude_none=True,
    status_code=201
)
async def add_zvr_to_service_work(
    service_work_id: int,
    zvr_number: Annotated[int, Field(ge=1_000_000, lt=10_000_000)],
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление 7-значного ЗВР к service_work."""
    service_work = await get_service_work(service_work_id, session)

    if not service_work:
        raise HTTPException(
            status_code=404,
            detail='Указанная работа не найдена.'
        )
    if service_work.zvr_number:
        raise HTTPException(
            status_code=422,
            detail='У данной работы ЗВР уже существует.'
        )
    if await check_zvr_unique(zvr_number, session):
        raise HTTPException(
            status_code=422,
            detail=f'Указанный ЗВР #{zvr_number} не уникален, сверьте данные.'
        )

    try:
        service_work.zvr_number = zvr_number
        service_work.zvr_create_date = dt.now()

        await session.commit()
        await session.refresh(service_work)  # Опционально
        return service_work
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            500,
            detail=f'Ошибка при сохранении ЗВР: {str(e)}'
        )


@router.patch(
    '/de_facto_completed',
    response_model=ServiceWorkWithZVRNumber,
    name='Работы выполнены, ждём закрытие ЗВР',
    description=(
        'Когда пользователь узнал, что работы выполнены, но по какой-то'
        ' причине сроки закрытия ЗВР неизвестны - пользователь вручную'
        ' закрывает ЗВР для конкретной сервисной работы.'
        'Примечание: данный функционал доступен только если ранее в системе'
        ' был указан ЗВР.'
    ),
    response_model_exclude_none=True,
    status_code=201
)
async def completed_real_service_work(
    service_work_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление признака фактического завершения работ в service_work."""
    service_work = await get_service_work(service_work_id, session)

    if not service_work:
        raise HTTPException(
            status_code=404,
            detail='Указанная работа не найдена.'
        )
    if not service_work.zvr_number:
        raise HTTPException(
            status_code=422,
            detail='Сначала необходимо добавить ЗВР.'
        )

    try:
        service_work.service_work_completed = True

        await session.commit()
        await session.refresh(service_work)  # Опционально
        return service_work
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            500,
            detail=(
                'Ошибка при указании информации'
                f'о фактическом завершении работ: {str(e)}'
            )
        )


@router.get(
    '/get_cars_service_work',
    response_model=list[ServiceWorkWithZVRNumber],
    response_model_exclude_none=True,
    name='Получение списка неархивных сервисных обслуживаний для ТС.',
)
async def get_all_active_service_works_list_by_current_car(
    car_id: int,
    request_status_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    return await get_active_service_work_list_by_car(
        car_id, request_status_id, session
    )


@router.get(
    '/get_summary_data_with_all_service_work',
    name=(
        'Получение (в моменте) общей статистики по всем расчётным статусам в'
        ' подразделении.'
    )
)
async def get_count_active_service_works_blya(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    return await get_active_service_work_count_for_all_service_status(
        organization_id, session
    )


@router.get(
    '/get_count_all_active_service_work_with_open_zvr',
    name=(
        'Получение (в моменте) количества зависших сервисных обслуживаний.'
    ),
    description=(
        'Выводится на экране подразделения (сверху) для понимания ситуации.'
    )
)
async def get_count_all_active_service_work_with_open_zvr(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> dict[str, int]:
    result = await get_all_active_service_work_with_open_zvr(
        organization_id, session
    )
    return {'active_service_work_with_open_zvr': len(result)}


@router.post(
    '/get_table',
    name='Получение главной таблицы.',
    description='Получение в виде списка списков.',
    response_model=list[list[Optional[ServiceWorkWithZVRNumber]]],
    response_model_exclude_none=True
)
async def get_table(
    request_status_id: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    return await create_main_table(
        request_status_id=request_status_id,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session
    )
