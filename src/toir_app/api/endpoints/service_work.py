from datetime import datetime as dt
from http import HTTPStatus
from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.endpoints.bot import TgSchedular
from core.db import get_async_session
from core.user import current_user
from crud.organization import get_current_organization
from crud.service_work import (
    check_users_can_edit_service_work,
    check_zvr_unique,
    create_main_table,
    get_active_service_work_count_for_all_service_status,
    get_active_service_work_list_by_car,
    get_all_active_service_work_with_open_zvr,
    get_db_status,
    get_service_work,
    update_completed_real_service_work
)
from models import Organization, SpecialStatus, User
from schemas.service_work import (
    AddZvrSchema,
    ServiceWorkWithZVRNumber,
)

router = APIRouter()


@router.get(
        '/current_date_in_db',
        name='Получение информации об актуальности базы данных.',
        status_code=HTTPStatus.OK,
)
async def get_newest_date(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Определение свежести данных (находит самую позднюю) в базе."""
    print(dt.now())
    return await get_db_status(session=session)


@router.patch(
    '/add_zvr',
    response_model=ServiceWorkWithZVRNumber,
    dependencies=[Depends(current_user)],
    name=(
        'Добавление `№ ЗВР` + `ID участка ТО` к конкретному `service_work`'
        ' (доступно сотруднику подразделения).'
    ),
    description=(
        '* если ЗВР создан - автоматически фиксируется дата создания\n'
        '* создать ЗВР повторно НЕЛЬЗЯ\n'
        '* ЗВР - всегда уникальное 7-значное число'
    ),
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED
)
async def add_zvr_to_service_work(
    zvr_attr: AddZvrSchema,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление 7-значного ЗВР и ID мастерской к карточке `service_work`."""
    service_work = await get_service_work(
        service_work_id=zvr_attr.service_work_id,
        session=session,
    )
    if service_work and service_work.zvr_number is not None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='У данной работы ЗВР уже существует.'
        )

    check_users_can_edit_service_work(user, service_work)
    await check_zvr_unique(zvr_attr.zvr_number, session)

    try:
        service_work.zvr_number = (
            f'{service_work.car.organization.name}-{zvr_attr.zvr_number}'
        )
        service_work.station_id = zvr_attr.station_id
        service_work.zvr_create_date = dt.now()  # TODO надо дописать tz

        await session.commit()
        await session.refresh(service_work)  # Опционально

        # schedular = TgSchedular(service_work)
        # await schedular.send_notification()

        return service_work
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при сохранении ЗВР: {str(e)}'
        )


@router.patch(
    '/de_facto_completed',
    response_model=ServiceWorkWithZVRNumber,
    dependencies=[Depends(current_user)],
    name=(
        'Работы выполнены, ждём закрытие ЗВР'
        '(доступно сотруднику подразделения)'
    ),
    description=(
        'Когда пользователь узнал, что работы выполнены, но по какой-то'
        ' причине сроки закрытия ЗВР неизвестны - пользователь вручную'
        ' закрывает ЗВР для конкретной сервисной работы.'
        'Примечание: данный функционал доступен только если ранее в системе'
        ' был указан ЗВР.'
    ),
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED
)
async def completed_real_service_work(
    service_work_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление признака фактического завершения работ в service_work."""

    result = await update_completed_real_service_work(
        add_date=True,
        service_work_id=service_work_id,
        user=user,
        session=session
    )

    # Отправка уведомления в Telegram:
    schedular = TgSchedular(result, event='done')
    await schedular.send_notification()

    return result


@router.patch(
    '/de_facto_drop',
    response_model=ServiceWorkWithZVRNumber,
    dependencies=[Depends(current_user)],
    name=(
        'Отмена фактического выполнения работы'
        '(доступно суперпользователю)'
    ),
    description='Для удаления ошибочных закрытий',
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED
)
async def drop_completed_real_service_work(
    service_work_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление признака фактического завершения работ в service_work."""
    return await update_completed_real_service_work(
        add_date=False,
        service_work_id=service_work_id,
        user=user,
        session=session
    )


@router.get(
    '/get_cars_service_work',
    response_model=list[ServiceWorkWithZVRNumber],
    response_model_exclude_none=True,
    name=(
        'Получение списка неархивных сервисных обслуживаний для ТС'
        ' (доступно всем).'
    ),
)
async def get_all_active_service_works_list_by_current_car(
    car_id: int,
    request_status_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    return await get_active_service_work_list_by_car(
        car_id=car_id,
        session=session,
        request_status_id=request_status_id
    )


@router.get(
    '/get_summary_data_with_all_service_work',
    name=(
        'Получение (в моменте) общей статистики по всем расчётным статусам в'
        ' подразделении (доступно всем).'
    ),
    description=(
        'Необходим для получения статистики по направлению ТО в целом по ЦП. '
        'Для точного понимания состояния необходимо передать ID спецстатусов, '
        'чтобы убрать, например, для подлежащих списанию или выставленных на '
        'продажу ТС сервисные работы.'
    ),
    response_model=Dict[str, Dict[str, int]]
)
async def get_count_active_service_works(
    special_status_list: List[Annotated[int, SpecialStatus.id]] = Query(
        description=(
            'Указать список ID специальных статусов, которые нужно включить '
            'в выборку.'
        )
    ),
    organization_id: Annotated[int, Organization.id] = Query(
        description='Указать ID подразделения', ge=0
    ),
    session: AsyncSession = Depends(get_async_session)
):
    if organization := await get_current_organization(
        organization_id=organization_id,
        session=session
    ):
        return await get_active_service_work_count_for_all_service_status(
            special_status_list=special_status_list,
            organization_id=organization.id,
            session=session
        )


@router.get(
    '/get_count_all_active_service_work_with_open_zvr',
    name=(
        'Получение (в моменте) количества зависших сервисных обслуживаний'
        ' (доступно всем).'
    ),
    description=(
        'Выводится на экране подразделения (сверху) для понимания ситуации.'
    )
)
async def get_count_all_active_service_work_with_open_zvr(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[dict[str, int]]:
    if organization := await get_current_organization(
        organization_id=organization_id,
        session=session
    ):
        result = await get_all_active_service_work_with_open_zvr(
            organization.id, session
        )
        return {'active_service_work_with_open_zvr': len(result)}
    return None


@router.post(
    '/get_table',
    name='Получение главной таблицы (доступно всем).',
    description=(
        'Получение в виде списка списков.'
        'Если юзер хочет скрыть сервисные операции, находящиеся в работе'
        ' (скрыть все записи с указанным ЗВР), он указывает'
        ' hide_service_work_with_zvr=True.'
    ),
    response_model=list[list[Optional[ServiceWorkWithZVRNumber]]],
    response_model_exclude_none=True
)
async def get_table(
    special_status_ids: list[Optional[int]] = Body(
        ...,
        description=(
            'Перечень ID специальных статусов ТС + все без статусов (None)'
        )
    ),
    request_status_id: int = Query(description='ID расчётного статуса'),
    organization_id: int = Query(description='ID подразделения (цеха)'),
    hide_service_work_with_zvr: bool = Query(
        default=False,
        description='True скрывает все записи с ЗВР'
    ),
    session: AsyncSession = Depends(get_async_session),
):
    return await create_main_table(
        request_status_id=request_status_id,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session,
        hide_service_work_with_zvr=hide_service_work_with_zvr
    )
