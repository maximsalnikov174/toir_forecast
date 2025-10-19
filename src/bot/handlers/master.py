from http import HTTPStatus

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.utils.markdown import hbold

from bot_command import BotCommand
from constants import KEYBOARD_MAX_ALIVE_IN_SECONDS
from common import get_button_text_from_state
from core.fsm_states import FSMForCar
from filters.service_work_filter import ServiceWorkFilter
from filters.user_filter import check_user_can_de_facto_close_service_work
from keyboards.common import create_task_for_delete_message_after_delay
from keyboards.kb_master import (
    build_back_button, build_done_button, build_zvr_list_buttons,
)
from lexicon import CommonAnswer
from services.gateway import backend_gateway

router = Router()


@router.message(F.text.startswith(f'/start {BotCommand.CAR.value}'))
async def get_cars_active_service_work(
    message: Message,
    state: FSMContext,
):
    """Получение инфы об активных ЗВР на ТС.

    Actions:
        Пользователь сканирует QR-код на ТС и получает список активных ЗВР.
    """
    await state.clear()  # сбрасываем состояние FSM

    async with backend_gateway as connector:
        if message.text:
            car_uuid = message.text.split(BotCommand.CAR.value)[1]
            if car_uuid.isascii():
                # Выполняем запросы к бэкенду:
                # - получаем информацию по ТС
                car = await connector.get_car_info(path=car_uuid)
                # - определяем полномочия текущего пользователя
                user_data = await connector.get_token(message.chat.id)

                # Если кто-то без аккаунта считал QR-код на ТС:
                if (
                    user_data
                    and user_data.get('status') == HTTPStatus.NOT_FOUND
                ):
                    await message.answer(f"Пока это просто {car.get('grz')}")
                    return

                await state.set_state(FSMForCar.service_work)  # установили

                # Сохранение состояния о ТС
                await state.update_data(
                    car_uuid=car_uuid,
                    car_grz=car.get('grz'),
                    user_permission=user_data['token'],
                    user_info=user_data['user'],
                    message_auto_delete=True,
                )

        service_works = await connector.get_service_work_for_current_car(
            car_attr=car_uuid,
            station_id=user_data['user']['users_organization']['station_id']
        )

        # Если работы есть (возможно, несколько):
        if len(service_works):
            buttons = await build_zvr_list_buttons(service_works, state)

            msg = f"{CommonAnswer.ACTIVE_WORKS}{hbold(car['grz'])}:"
            answer_message = await message.answer(
                msg,
                reply_markup=buttons.as_markup(),
                parse_mode=ParseMode.HTML,
            )

        else:
            answer_message = await message.answer(CommonAnswer.NO_DATA)

        # Создание задач для очистки сообщений после некоторого времени:
        await create_task_for_delete_message_after_delay(message=message)

        await create_task_for_delete_message_after_delay(
            message=answer_message,
            delay=KEYBOARD_MAX_ALIVE_IN_SECONDS,
        )


@router.callback_query(ServiceWorkFilter(BotCommand.SERVICE_WORK))
async def handle_service_work(
    callback: CallbackQuery,
    state: FSMContext,
    service_work_id: int  # Данные перехватывает ServiceWorkFilter
):
    """Действие с выбранным мастером цеха ремонта активным ЗВР (работой)."""
    # Дополняем FSM выбранной пользователем работой (pk):
    await state.update_data(service_work_id=service_work_id)

    # ... и сообщением:
    car = await get_button_text_from_state(
        state=state,
        storage_key='car_grz',
    )
    service_work_info_on_button = await get_button_text_from_state(
        state=state,
        storage_key='button_mapping',
        callback=callback,
    )
    msg = f'Объект «{hbold(car)}»\n🛠️ {hbold(service_work_info_on_button)}\n'
    await state.update_data(msg=msg)

    # TODO Получение данных об использованных материалах:
    total_bom = []
    async with backend_gateway as connector:
        materials = await connector.get_bom_for_service_work(service_work_id)
        if delivery := materials.get('docs_in_service_work'):
            for el_delivery in delivery:
                el_data = el_delivery.get('components')
                for el in el_data:
                    total_bom.append(f"{el['snb']} {el['material_name']}")

    # FIXME Пока с этим ничего не надо будет делать:
    print(total_bom)

    # Редактируем сообщение и клавиатуру:
    await callback.message.edit_text(
        text=f'{msg}Что делаем?',
        parse_mode=ParseMode.HTML,
    )

    await callback.message.edit_reply_markup(
        reply_markup=(await build_done_button(state)).as_markup()
    )


@router.callback_query(F.data == BotCommand.SERVICE_WORK_DONE.value)
async def complete_service_work(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Завершение выбранной работы (ЗВР)."""
    async with backend_gateway as connector:
        # Получаем из FSM токен пользователя:
        connector.token = (
            (await state.get_value('user_permission')).get('access_token')
        )

        if service_work_id := await state.get_value('service_work_id'):

            # Блок проверки прав пользователя с выводом "не пройдешь!":
            if not await check_user_can_de_facto_close_service_work(
                state=state,
                service_work_id=service_work_id,
            ):
                msg = await callback.message.edit_text(
                    text=CommonAnswer.NO_PERMISSION,
                    reply_markup=(await build_back_button(state)).as_markup(),
                )
                if isinstance(msg, Message):
                    await create_task_for_delete_message_after_delay(msg, 10)

            else:
                result = await connector.completed_real_service_work(
                    service_work_id=service_work_id,
                )

                if result.get('status') == HTTPStatus.BAD_REQUEST:
                    msg = CommonAnswer.TO_LATE,
                else:
                    msg = f"{await state.get_value('msg')}Завершено!"
                # игнорируя task, удаляем сообщение с клавиатурой
                await callback.message.delete()

                # ... и фиксируем результат сообщением (уже без его удаления):
                await callback.message.answer(
                    text=msg,
                    parse_mode=ParseMode.HTML,
                )


@router.callback_query(F.data == BotCommand.SERVICE_WORK_BACK.value)
async def back_to_active_service_work_list(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Возвращение на шаг с выбором активных ЗВР на ТС.

    Actions:
        Пользователь, находясь внутри выбранного ЗВР, нажал кнопку `назад`.
    """
    fsm_data = await state.get_data()
    user_data = fsm_data.get('user_info')
    station_id = user_data['users_organization']['station_id']

    async with backend_gateway as connector:
        data = await connector.get_service_work_for_current_car(
            car_attr=fsm_data.get('car_uuid'),
            station_id=station_id,
        )

        # Если работы есть (возможно, несколько):
        if len(data):
            buttons = await build_zvr_list_buttons(data, state)
            msg = (
                f"{CommonAnswer.ACTIVE_WORKS}{hbold(fsm_data.get('car_grz'))}:"
            )
        else:
            msg = CommonAnswer.NO_DATA

        await callback.message.edit_text(
            text=msg,
            reply_markup=buttons.as_markup() if buttons else None,
            parse_mode=ParseMode.HTML,
        )


@router.message(CommandStart())
async def command_get_data_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка команды начала взаимодействия с ботом."""
    try:
        # await state.clear()  # сбрасываем состояние FSM

        # # Проверка прав доступа к чату:
        # if not await check_users(id=message.chat.id):
        #     await message.answer(LEX[CommandForBot.NOT_ACCESS])

        await message.answer('Будем знакомы')

    except Exception:
        await message.answer('Sorry')
