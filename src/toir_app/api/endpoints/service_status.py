from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from crud.service_status import (
    get_multi_service_status, dao_service_status,
)
from exception import ObjectIsExistException, ObjectNotFoundException
from schemas.service_status import ServiceStatusSchema, ServiceStatusUpdate

router = APIRouter()


@router.get(
    '/all',
    response_model=list[ServiceStatusSchema],
    name=('Список расчётных статусов (доступно всем)'),
    description=(
        'Получение списка всех расчётных статусов для сервисного'
        ' обслуживания.'
    ),
    status_code=200,
)
async def get_all_service_status(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_multi_service_status(session)


@router.patch(
    '/{service_status_id}',
    response_model=ServiceStatusSchema,
    response_model_exclude_none=True,
    name='Обновление имени расчётного статуса (доступно всем)',
)
async def update_service_status(
    service_status_id: int,
    obj_in: ServiceStatusUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        service_status = (
            await dao_service_status.get(service_status_id, session)
        )

        if not service_status:
            raise ObjectNotFoundException

        # Если для обновления передается поле `name`:
        if obj_in.name is not None:
            await dao_service_status.check_name_duplicate(obj_in.name, session)

        service_status = await dao_service_status.update(
            db_obj=service_status,
            obj_in=obj_in,
            session=session
        )

        return service_status

    except ObjectNotFoundException:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f'Расчётный статус с ID#{service_status_id} не найден',
        )

    except ObjectIsExistException:
        raise HTTPException(
            HTTPStatus.CONFLICT,
            detail=f'Название «{obj_in.name}» уже используется',
        )
