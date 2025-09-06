import re
from datetime import date, timedelta
from http import HTTPStatus
from typing import Annotated, Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from constants import MAX_SPECIAL_STATUS_VALID, pattern_grz_input_user
from crud.special_status import get_special_status_by_id
from exception import (
    AlreadyAssignedException,
    CarInArchiveException,
    CarNotFoundException,
    NoPermissionForActionException,
    NotFoundError
)
from logger.logger import logger
from models import (
    Car,
    ServiceWork,
    SpecialStatusForCar,
    User,
    UserRole,
)
from schemas.car import CarToDownloadInDB
from schemas.car_model import CarModelID
from schemas.organization import OrganizationID


async def get_car_by_personal_id(
        personal_id: int,
        session: AsyncSession
) -> Optional[Car]:
    """Получаем запись о Car по OeBS personal_id."""
    return await session.scalar(
        select(Car).where(Car.personal_id == personal_id)
    )


async def get_car_by_pk(
        car_id: int,
        session: AsyncSession,
        check_car_in_archive: bool = True,
        expand_data: bool = False
) -> Optional[Car]:
    """Получаем запись о Car по PK.

    ### Args:
    - check_car_in_archive: проверяет ТС, переведенные в архив;
    - expand_data: получение связанных данных(специальные статусы ТС).

    ### Returns:
        - объект модели Car

    ### Exceptions:
        - 404 если ТС не найдено
        - 400 если ТС находится в архиве
    """
    if expand_data:
        car = await session.scalar(
            select(Car)
            .options(selectinload(Car.status_associations))
            .where(Car.id == car_id)
        )
    else:
        car = await session.get(Car, car_id)

    if not car:
        raise CarNotFoundException

    if check_car_in_archive and car.in_archive:
        raise CarInArchiveException

    return car


async def get_all_active_car_list(
        session: AsyncSession
) -> list[Car.id]:
    """Получаем список ID всех активных Car (со статусом «не в архиве»)."""
    result = await session.scalars(
        select(Car.id)
        .where(Car.in_archive.is_(False))
    )
    return list(result)


async def push_cars_in_archive(
        cars_in_file: set[int],
        session: AsyncSession
) -> set[int]:
    """Сбор всех непереданных в отчёте RMT321 ТС и перевод их в архив."""
    car_list_in_db = await get_all_active_car_list(session=session)
    cars_list_in_archive = set(car_list_in_db) - set(cars_in_file)

    if cars_list_in_archive:
        logger.info(f'Начало архивирования {len(cars_list_in_archive)} ТС:')

        for car_id in cars_list_in_archive:
            await add_car_in_archive(car_id=car_id, session=session)

        logger.info(
            f'Архивирование {len(cars_list_in_archive)} ТС завершено.'
        )

    # await session.commit()
    return cars_list_in_archive


async def add_car_in_archive(
        car_id: int,
        session: AsyncSession
) -> None:
    """Архивирование (без коммита) Car."""
    car: Optional[Car] = await get_car_by_pk(car_id=car_id, session=session)
    if car:
        car.in_archive = True
        session.add(car)
        logger.info(f'🫡 🚚 ТС «{car.grz}» перенесено в архив.')


async def get_car_by_full_grz(
        grz: str,
        session: AsyncSession
) -> Car:
    """
    Получаем запись о Car по ГРЗ (без учета пробелов).

    Прогоняем ГРЗ по паттерну А 123 АВ или АВ 1234 74/174/774, после чего
    получаем запись.

    Exceptions:
        - 404 если указанный ГРЗ не соответствует базовым паттернам ГРЗ.
        - 404 если ТС с указанным валидным ГРЗ не найден.
    """
    match = re.match(pattern_grz_input_user, grz.upper())
    if not match:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Проверьте формат ГРЗ!'
        )
    groups_grz = match.groups()
    clear_grz = ' '.join(filter(None, groups_grz))  # убрали None из groups

    car = await session.scalar(
        select(Car)
        .where(
            # Car.grz.startswith(grz),  # ГРЗ начинается с ...
            Car.grz == clear_grz,
            Car.in_archive.is_(False)
        ).options(
            joinedload(Car.organization),
            joinedload(Car.car_model),
            joinedload(Car.status_associations)
        )
    )
    if not car:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='ТС не найдено!'
        )
    return car


async def get_cars_with_request_and_special_status(
    session: AsyncSession,
    *,
    hide_service_work_with_zvr: bool = False,
    for_masters: bool = False,
    request_status_id: Optional[int] = None,
    special_status_ids: Optional[list[Optional[int]]] = None,
    organization_id: int,
    user: Optional[User] = None,
) -> list[Optional[Car]]:
    """
    Возврат УНИКАЛЬНЫХ машин c учётом выбранных пользователем фильтров.

    ## Variants:
    - для мастерской `for_master=True`
    - для автоколонны

    ## Filters:
        - расчётный статус (он и строже)
        - все ТС без статусов (FIXME пока обязательно)
        - список специальных статусов (опционально)
    """
    stmt = (
        select(Car)
        .options(
            selectinload(Car.car_model),
            selectinload(Car.status_associations),
            selectinload(Car.service_works)
        )
        .join(Car.service_works)  # Явное соед. с service_works
        .outerjoin(Car.status_associations)  # статусы могут отс.
        .outerjoin(SpecialStatusForCar.special_status)  # присоединяем статусы
        .where(
            ServiceWork.in_archive.is_(False),
            Car.in_archive.is_(False),
        ).distinct()  # distinct - дедупликация (FIXME не уверен, что так)
        .order_by(Car.grz)
    )

    if for_masters and user:  # если пользователь - сотрудник цеха ремонта:
        stmt = stmt.where(
            ServiceWork.station_id == organization_id,
            ServiceWork.zvr_number.is_not(None),
        )
        if user.users_role.name == UserRole.MASTER.value:
            # - поле «работа завершена фактически» не заполнено
            stmt = stmt.where(ServiceWork.service_work_completed.is_(None))

        elif user.users_role.name == UserRole.OPERATOR.value:
            # - поле «работа завершена фактически» не пустое
            stmt = stmt.where(ServiceWork.service_work_completed.is_not(None))

    # если пользователь - сотрудник цеха эксплуатации:
    # - нужны только ТС своего цеха и
    # - расчётные статус "указанный и строже" и
    # - или у ТС нет специальных статусов
    # - или у ТС специальный статус истёк
    # - или у ТС специальный статус "активный" и находится в указанном перечне
    else:
        stmt = stmt.where(
            Car.organization_id == organization_id,
            ServiceWork.request_status_id <= request_status_id,
            or_(
                SpecialStatusForCar.car_id.is_(None),
                SpecialStatusForCar.is_active.is_(False),
                and_(
                    SpecialStatusForCar.special_status_id.in_(
                        special_status_ids
                    ),
                    SpecialStatusForCar.is_active.is_(True),
                )
            )
        )

        # ... и ему надо cкрыть записи о серв.обсл., если для них создан ЗВР:
        if hide_service_work_with_zvr:
            stmt = stmt.where(ServiceWork.zvr_number.is_(None))

    cars = await session.execute(stmt)

    return list(cars.unique().scalars().all())  # получение уникальных cars


async def add_special_status_to_car(
        special_status_id: int,
        car_id: int,
        user: User,
        date_from_user: date,
        session: AsyncSession,
        comment: Optional[str] = None
) -> Optional[Car]:
    """Устанавливает специальный статус для ТС.

    Returns:
        - объект модели Car.
        - None.

    Exceptions:
        - 400 если выбранный статус и так равен текущему.
        - 403 если у пользователя недостаточно прав.
        - 404 если ID выбранного статуса нет в списке статусов.
        - 500 если случились прочие проблемы.
    """
    if date_from_user <= date.today():
        raise HTTPException(HTTPStatus.BAD_REQUEST, 'Укажите дату в будущем!')
    elif date_from_user >= date.today() + timedelta(MAX_SPECIAL_STATUS_VALID):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'Давайте так: специальный статус для ТС действует '
            f'не больше {MAX_SPECIAL_STATUS_VALID} дней!'
        )

    try:
        # Проверяем, существует ли special_status и car по их id:
        special_status = await get_special_status_by_id(
            special_status_id=special_status_id,
            session=session,
            expand_data=True
        )

        car = await get_car_by_pk(car_id, session, expand_data=True)

        allowed_roles = (
            [users_role.id for users_role in special_status.allowed_roles]
        )

        # Проверяем права пользователя для установки выбранного статуса:
        if user.role_id not in allowed_roles:
            raise NoPermissionForActionException

        if (
            car.organization_id != user.organization_id
            and not user.is_superuser
        ):
            raise NoPermissionForActionException

        active_status_car = {
            elem.special_status_id: elem.date_left
            for elem in car.status_associations
            if elem.is_active
        }

        if special_status_id in active_status_car.keys():
            raise AlreadyAssignedException

        element = SpecialStatusForCar()
        element.car_id = car_id
        element.special_status_id = special_status_id
        element.assigned_by_user_id = user.id
        element.comment = comment
        element.date_left = date_from_user
        element.is_active = True

        session.add(element)
        await session.flush()
        await session.refresh(car)  # Обновляем объект из БД
        await session.commit()
        return await get_car_by_pk(car_id, session, expand_data=True)

    except CarNotFoundException:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.NO_CONTENT,
            'ТС не найдено'
        )

    except CarInArchiveException:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'ТС находится в архиве, действие невозможно'
        )

    except NotFoundError:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.NO_CONTENT,
            'Специальный статус не найден'
        )

    except NoPermissionForActionException:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'Специальный статус невозможно установить с данными правами юзера'
        )

    except AlreadyAssignedException:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'Выбранный статус ТС уже назначен '
            f'и действует до {active_status_car[special_status_id]}'
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при обновлении статуса ТС: {str(e)}'
        )


async def get_car_history(
        car_id: Annotated[int, Car.id],
        session: AsyncSession
):
    """Получение истории по выполненным сервисным обслуживаниям для ТС."""
    await get_car_by_pk(car_id=car_id, session=session)

    # FIXME не обрабатывается ситуация, когда указанное ТС находится в архиве!

    stmt = (
        select(ServiceWork)
        .where(
            ServiceWork.car_id == car_id,
            ServiceWork.in_archive.is_(True)
        )
    )
    stmt = (
        stmt.options(selectinload(ServiceWork.station))
        .order_by(
            ServiceWork.request_reading,
            ServiceWork.last_service_id  # чтоб всегда был один порядок
        )
    )
    return await session.scalars(stmt)


async def get_or_create_car_and_return_id(
    session: AsyncSession,
    personal_id: int,
    grz: str,
    car_model: CarModelID,
    organization: OrganizationID
) -> tuple[int, str]:
    """Получает экземпляр модели Car или создает его (автомобиль)."""
    car_in_db = await get_car_by_personal_id(personal_id, session)

    if not car_in_db:
        # загоняем в pydantic-схему:
        validated_car = CarToDownloadInDB(
            personal_id=personal_id,
            grz=grz,
            car_model_id=car_model.id,
            organization_id=organization.id
        )
        new_car: dict[str, Any] = validated_car.model_dump()

        # создаем экземпляр модели Car и добавляем в сессию:
        car: Car = Car(**new_car)
        session.add(car)
        await session.commit()
        await session.refresh(car)
        logger.info(f'🚚 «{car.grz}» создано.')
        return car.id, car.grz

    else:
        # Проверяем прописку ТС в подразделении:
        if car_in_db.organization_id != organization.id:
            car_in_db.organization_id = organization.id
            logger.info(f'ТС {grz} изменило прописку на {organization}')
            session.add(car_in_db)

    return car_in_db.id, car_in_db.grz
