import hashlib
from calendar import monthrange
from datetime import datetime as dt

from fastapi import UploadFile

from constants import PATTERN_DATE_OEBS
from exception import (
    BadTypeUploadFileException,
    BiggestFileException,
    FilesHashSumNotUniqueException,
)


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


def add_declension_to_date(value: int) -> str:
    """Добавляет к слову `день` склонение и возвращает фразу целиком."""
    if value % 10 == 1 and not value // 10 % 10 == 1:
        word = 'день'
    elif 2 <= value % 10 <= 4 and not value // 10 % 10 == 1:
        word = 'дня'
    else:
        word = 'дней'

    return f'{value} {word}'


async def calc_pdf_hashsum(
        upload_file: UploadFile,
        size_in_mb: int = 2,
        algo='sha256',
) -> str:
    """Расчитывает хеш-сумму файла pdf размером до 2 Mb."""
    if upload_file.content_type != 'application/pdf':
        raise BadTypeUploadFileException

    content = await upload_file.read()
    if len(content) > size_in_mb * 1024 * 1024:
        await upload_file.seek(0)  # Возвращаем указатель чтения fastapi-файла
        raise BiggestFileException(f'Файл слишком большой: {len(content)} Б.')

    hash_func = hashlib.new(algo)
    hash_func.update(content)

    # Возвращаем указатель на начало fastapi.UploadFile-файла
    await upload_file.seek(0)

    return hash_func.hexdigest()


async def compare_files(elements=list[UploadFile]) -> list[UploadFile]:
    """Сравнивает хеш-суммы поданных файлов.

    RAISES
        FilesHashSumNotUniqueException: если нашлись дубли.

    RETURN
        список файлов с уникальными хеш-суммами.
    """
    hashes = set()

    result: list[UploadFile] = []

    for element in elements:
        try:
            file_hash = await calc_pdf_hashsum(element)

            if file_hash in hashes:
                raise FilesHashSumNotUniqueException

            hashes.add(file_hash)  # обновляем список хеш-сумм
            result.append(element)  # добавляем файл к успешно пройденным
        except BadTypeUploadFileException:
            continue

    return result
