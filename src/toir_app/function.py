from datetime import datetime as dt
from calendar import monthrange

from constants import PATTERN_DATE_OEBS


def convert_date(string: str) -> dt:
    """
    Из строки вида ДД.ММ.ГГГГ ЧЧ:ММ:СС делает объект datetime.
    """
    return dt.strptime(string, PATTERN_DATE_OEBS)


def predict_reading_when_current_month_left(
    current_date: dt,
    daily_distance: float,
    reading_now: float
) -> float:
    """
    Прогнозируем наступление события в текущем месяце с учетом ср.сут пробега.
    """
    # Дней в текущем месяце:
    days_in_month = monthrange(current_date.year, current_date.month)[1]

    days_left = days_in_month - current_date.day

    # !!! TODO !!!
    # if daily_distance == 0:
    #     надо указать, что машина без движения,
    #     потому что следующее обслуживание не наступит никогда

    forecast_reading = days_left * daily_distance
    return forecast_reading + reading_now
