from aiogram.fsm.state import default_state, State, StatesGroup


class FSMForCar(StatesGroup):
    """Хранилище инфы по ТС."""

    service_work = State()
