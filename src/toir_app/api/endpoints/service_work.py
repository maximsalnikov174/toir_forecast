from datetime import datetime as dt
from http import HTTPStatus
from typing import Annotated, Dict, List, Optional

from fastapi import (
    APIRouter, Body, Depends, HTTPException, Query, status, UploadFile
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.endpoints.bot import bot_schedular
from convert_pdf_to_py.unit_of_bom import get_payload_data_in_pdf_file
from core.db import get_async_session
# from core.minio import get_minio_client
from core.user import current_user, current_superuser
from crud.docs_material import dao_doc_bom, dao_unit_of_bom
from crud.organization import dao_organization, get_current_organization
from crud.service_work import (
    check_user_can_add_docs_in_service_work,
    check_users_can_edit_service_work,
    check_zvr_unique,
    create_main_table,
    create_main_table_for_master,
    dao_service_work,
    get_active_service_work_count_for_all_service_status,
    get_active_service_work_list_by_car,
    get_all_active_service_work_with_open_zvr,
    get_db_status,
    update_completed_real_service_work,
    zvr_delete
)
from exception import ObjectIsExistException
from models import EventForBot, Organization, SpecialStatus, User
# from schemas.docs_material import BOMRead
from schemas.service_work import (
    AddZvrSchema,
    ServiceWorksBOMListAndCarOrganization,
    ServiceWorkWithBOMList,
    ServiceWorkWithZVRNumber,
)
from schemas.unit_of_bom import (
    BOMDocsCreate,
    UnitOfBOMRead,
    UnitOfBOMWithDocsCreate,
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
    service_work = await dao_service_work.get_service_work(
        obj_id=zvr_attr.service_work_id,
        session=session,
    )
    if service_work and service_work.zvr_number is not None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='У данной работы ЗВР уже существует.'
        )

    check_users_can_edit_service_work(user=user, service_work=service_work)
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
    await bot_schedular.send_notification(obj=result, event=EventForBot.DONE)

    return result


@router.patch(
    '/de_facto_drop',
    response_model=ServiceWorkWithZVRNumber,
    dependencies=[Depends(current_superuser)],
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
    """Удаление признака фактического завершения работ в service_work."""
    return await update_completed_real_service_work(
        add_date=False,
        service_work_id=service_work_id,
        user=user,
        session=session
    )


@router.patch(
    '/zvr_drop',
    response_model=ServiceWorkWithZVRNumber,
    dependencies=[Depends(current_superuser)],
    name=(
        'Удаление ЗВР из работы'
        '(доступно суперпользователю)'
    ),
    description='Для удаления ошибочно или неверно указанных ЗВР',
    response_model_exclude_none=True,
    status_code=HTTPStatus.CREATED
)
async def drop_zvr_from_service_work(
    service_work_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    return await zvr_delete(
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
    response_model=list[list[Optional[ServiceWorkWithBOMList]]],
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


@router.post(
    '/get_table_for_master',
    name='Получение главной таблицы (доступно мастерским).',
    description=(
        'Получение в виде списка списков.'
    ),
    response_model=list[list[Optional[ServiceWorkWithBOMList]]],
    response_model_exclude_none=True
)
async def get_table_for_master(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await create_main_table_for_master(
        user=user,
        session=session,
    )


# @router.post(
#     '/{service_work_id}/bom',  # /service_work/1/bom
#     response_model=BOMRead,
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(current_user)]
# )
# async def upload_docs(
#     service_work_id: int,
#     file: UploadFile,
#     session: AsyncSession = Depends(get_async_session),
# ):
#     """Отправка документа в карточку операции."""
#     service_work = await dao_service_work.get_with_docs(
#         obj_id=service_work_id,
#         session=session,
#     )

#     if service_work is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f'Карточка работы #{service_work_id} не найдена',
#         )

#     client = get_minio_client()

#     return await dao_bom.create_with_file(
#         service_work_id=service_work_id,
#         file=file,
#         client=client
#     )


@router.get(
        '/{service_work_id}/unit_of_bom',
        response_model=ServiceWorksBOMListAndCarOrganization,
        status_code=status.HTTP_200_OK,
        name='Получение списка документов с материалами (доступно всем).',
        response_model_exclude_none=True,
)
async def get_docs(
    service_work_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Получение списка документов к карточке операции."""
    try:
        service_work = await dao_service_work.get(
            obj_id=service_work_id,
            session=session,
        )

        if service_work is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Карточка работы #{service_work_id} не найдена',
            )

        # Подгружаем документы к `service_work` для вывода результата:
        await dao_doc_bom.get_multi_by_attribute(
            attr_name='service_work_id',
            attr_value=service_work_id,
            session=session,
        )
        return service_work

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Непредвиденная ошибка: {e}',
        )


@router.post(
    '/unit_of_bom/{bom_id}',
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_user)],
    name='Фиксация оператором мастерской внесения материалов в ЗВР.'
)
async def insert_docs(
    bom_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Фиксация внесения материалов в ЗВР."""
    try:
        # Проверяем карточку с документами:
        doc_bom = await dao_doc_bom.get_full(obj_id=bom_id, session=session)
        if doc_bom is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Карточка с документами #{bom_id} не найдена',
            )

        # Проверяем существование работы:
        service_work = await dao_service_work.get_service_work(
            obj_id=(service_work_id := doc_bom.service_work_id),
            session=session,
        )

        # Проверяем права пользователя (может только оператор):
        check_users_can_edit_service_work(
            user=user,
            service_work=service_work,
            for_station=True,
            operator_leniency=True  # послабление прав для оператора
        )

        # Переводим карточку doc_bom в статус выполнено:
        doc_bom.to_insert = True
        await session.commit()

        # Проверка, что с service_work больше не связаны никакие документы
        docs_exists = await dao_doc_bom.check_constrained_docs(
            service_work_id=service_work_id,
            session=session
        )
        # ... если больше документов не осталось:
        if not docs_exists:
            # ... можно отправлять уведомление:
            await bot_schedular.send_notification(
                obj=service_work,
                event=EventForBot.DOC_INSERT
            )
            # Переводим карточку service_work в статус «доки оформлены»:
            service_work.to_insert = True
            await session.commit()
            return True
        return False

    except Exception:
        pass


@router.post(
    '/unit_of_bom',
    response_model=UnitOfBOMRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_user)]
)
async def parse_docs(
    service_work_id: int,
    file: UploadFile,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Отправка документа в карточку операции."""
    try:
        service_work = await dao_service_work.get(
            obj_id=service_work_id,
            session=session,
        )

        if service_work is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Карточка работы #{service_work_id} не найдена',
            )
        if service_work.zvr_create_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Работа #{service_work_id} еще не связана с ЗВР',
            )

        # Проверка нескольких прав пользователя:
        # 1. Только работы, связанные с мастерской сотрудника:
        check_users_can_edit_service_work(user, service_work, for_station=True)
        # 2. Только для пользователя с ролью Мастер/Оператор/суперюзер:
        check_user_can_add_docs_in_service_work(user)

        # Получаем данные из файла pdf и загоняем их в модель:
        data = await get_payload_data_in_pdf_file(file=file)

        # Находим подразделение (нужен ID), указанное в документах, в БД:
        organization = await dao_organization.get_by_attribute(
            attr_name='name',
            attr_value=data.unit_of_bom_doc.from_organization,
            session=session
        )

        # Проверяем, что ID доставки и указанный штрих-код уникальны:
        await dao_doc_bom.check_exists(
            attr_name='delivery',
            attr_value=getattr(data.unit_of_bom_doc, 'delivery'),
            session=session,
        )

        await dao_doc_bom.check_exists(
            attr_name='bar_code',
            attr_value=getattr(data, 'bar_code'),
            session=session,
        )

        # Создаем объект документа BOM:
        bom_doc = BOMDocsCreate(
            delivery=data.unit_of_bom_doc.delivery,
            from_organization=organization.id,
            service_work_id=service_work_id,
            user_id=user.id,
            bar_code=data.bar_code,
        )
        bom = await dao_doc_bom.create(obj_in=bom_doc, session=session)

        # Создаем записи о материалах, указанные в документах:
        for unit in data.unit_of_bom_list:
            uob_for_create = UnitOfBOMWithDocsCreate(
                snb=unit.snb,
                material_name=unit.material_name,
                material_count=unit.material_count,
                maintenance_bom_id=bom.id
            )
            await dao_unit_of_bom.create(
                obj_in=uob_for_create,
                session=session,
            )

        # FIXME!!! Как решить проблему отката назад, если что-то пошло не так?

        # Получаем обновленную карточку документа с материалами:
        return await dao_doc_bom.get_full(obj_id=bom.id, session=session)

    except ObjectIsExistException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Данные в файле PDF не уникальны (что недопустимо)',
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Непредвиденная ошибка: {e}',
        )
