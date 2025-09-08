from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_superuser
from crud.role import dao_role
from models import Role
from schemas.role import RoleCreate, RoleBase

router = APIRouter()


@router.post(
    '',
    response_model=RoleBase,
    name='Создание новой роли (только админ)',
    description='Для расширения списка ролей пользователей.',
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(current_superuser)],
    response_model_exclude_none=True,
)
async def create_new_role(
    obj_in: RoleCreate,
    session: AsyncSession = Depends(get_async_session),
) -> Role:
    """Создание новой роли."""
    try:
        # Валидация на уровне pydantic:
        # FIXME пока не обрабатывается резульат!

        # Проверяем уникальность поля `name`:
        role_exist = (
            await dao_role.get_by_attribute('name', obj_in.name, session)
        )
        if role_exist:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                f'Роль с именем {obj_in} уже есть.'
            )

        return await dao_role.create(obj_in, session)

    except Exception:
        raise
