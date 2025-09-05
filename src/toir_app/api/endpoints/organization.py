from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_superuser
from crud.organization import (
    get_current_organization,
    get_organization_list,
    dao_organization,
)
from crud.station import dao_station
from models import Organization
from schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter()


@router.get(
    '/all',
    response_model=list[OrganizationResponse],
    name='Получение списка подразделений (на выбор пользователю)',
    description='Получение списка всех подразделений для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_all_organization(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_organization_list(session)


@router.patch(
    '/{organization_id}',
    response_model=OrganizationResponse,
    name='Обновление подразделения (только админ)',
    description='Для изменения подразделения.',
    status_code=HTTPStatus.OK,
    dependencies=[Depends(current_superuser)],
    response_model_exclude_none=True,
)
async def update_organization(
    organization_id: int,
    obj_in: OrganizationUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> Organization:
    """Обновление подразделения (пока только `station_id`)."""
    try:
        # Проверяем существование `organization_id`:
        org_exist = await dao_organization.get(organization_id, session)
        if not org_exist:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                f'Организация с ID#{organization_id} не найдена.'
            )

        # Проверяем существование `station_id` (если оно указано):
        if obj_in.station_id:
            station_exist = await dao_station.get(obj_in.station_id, session)
            if not station_exist:
                raise HTTPException(
                    HTTPStatus.BAD_REQUEST,
                    f'Станция с id#{obj_in.station_id} не найдена.'
                )

        return await dao_organization.update(
            db_obj=org_exist,
            obj_in=obj_in,
            session=session,
        )

    except Exception:
        raise


@router.post(
    '',
    response_model=OrganizationResponse,
    name='Создание нового подразделения (только админ)',
    description='Для расширения списка подразделений.',
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(current_superuser)],
    response_model_exclude_none=True,
)
async def create_new_organization(
    obj_in: OrganizationCreate,
    session: AsyncSession = Depends(get_async_session),
) -> Organization:
    """Создание нового подразделения."""
    try:
        # Валидация на уровне pydantic:
        # FIXME пока не обрабатывается резульат!

        # Проверяем уникальность полей `name` и `normal_name`:
        check_attr = {
            'name': obj_in.name,
            'normal_name': obj_in.normal_name,
        }
        for k, v in check_attr.items():
            org_exist = await dao_organization.get_by_attribute(k, v, session)
            if org_exist:
                raise HTTPException(
                    HTTPStatus.BAD_REQUEST,
                    f'Организация с полем {v} ({k}) уже есть.'
                )

        # Проверяем существование `station_id` (если оно указано):
        if obj_in.station_id:
            station_exist = await dao_station.get(obj_in.station_id, session)
            if not station_exist:
                raise HTTPException(
                    HTTPStatus.BAD_REQUEST,
                    f'Станция с id {obj_in.station_id} не найдена.'
                )

        # FIXME могут ли разные подразделения быть связаны с одной станцией?????
        # FIXME в зависимости от этого решить, стоит ли проверять существование
        # FIXME подразделения, связанного с указанной станцией.

        return await dao_organization.create(obj_in, session)

    except Exception:
        raise


@router.get(
    '/with_vehicles',
    response_model=list[OrganizationResponse],
    name='Получение списка подразделений (на выбор пользователю)',
    description='Получение списка всех подразделений для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_all_vehicles_organization(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_organization_list(session, vehicle_only=True)


@router.get(
    '/{organization_id}',
    response_model=OrganizationResponse,
    name='Получение информации о выбранном пользователем подразделении',
    description='Получение подразделения для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает выбранное пользователем подразделение."""
    return await get_current_organization(organization_id, session)
