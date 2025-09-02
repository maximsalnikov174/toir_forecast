import re
from typing import Union

from constants import PATTERT_DISCHARGE_INT_VALUE


def convert_value_with_discharge(value: Union[int, float]) -> str:
    """Разделяет целое число на число-строку, разделенную разрядами."""
    if isinstance(value, float):
        integer_part, _, fractional_part = str(value).partition('.')
    elif isinstance(value, int):
        integer_part = str(value)
        fractional_part = str(0)

    formatted_integer = (
        re.sub(PATTERT_DISCHARGE_INT_VALUE, r'\1 ', str(integer_part))
    )
    return str(f'{formatted_integer}.{fractional_part}')
