from aiogram.fsm.context import FSMContext


async def check_user_can_de_facto_close_service_work(
        state: FSMContext,
        service_work_id: int,
) -> bool:
    """Фильтр, который проверит права пользователя для закрытия ЗВР.

    Checking:
        - `is active` and `is_verified`
        - `is_superuser | user.station_id == service_work.station_id`
    """
    data = await state.get_data()

    # Базовые проверки
    if not (user := data.get('user_info')):
        return False

    # Проверка активного и верифицированного пользователя
    if not (user.get('is_active') and user.get('is_verified')):
        return False

    # Суперпользователь имеет доступ
    if user.get('is_superuser'):
        return True

    # Проверка что `station_id` существует у пользователя
    user_org = user.get('users_organization')
    if not user_org or 'station_id' not in user_org:
        return False

    # Проверка что `station_info` существует в данных
    station_info = data.get('station_info')
    if not station_info or service_work_id not in station_info:
        return False

    return user_org['station_id'] == station_info[service_work_id]
