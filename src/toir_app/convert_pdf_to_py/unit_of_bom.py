import json
import re
from io import BytesIO
from typing import Optional

import pdfplumber
from fastapi import UploadFile
from pydantic import ValidationError

from constants import EXTRUDE_SYMBOLS_IN_HEADER
from exception import InsufficientDataError
from schemas.unit_of_bom import UnitOfBOM as UnitOfBOMSchema


target_headers = {
    'delivery': 'номердоставки',
    'snb': 'номенклатурныйномер',
    'material_name': 'наименование',
    'material_count': 'колвозапрошено',
    'from_organization': 'организацияполучатель',
}


async def get_payload_data_in_pdf_file(
        file: UploadFile,
) -> Optional[list[UnitOfBOMSchema]]:
    """Сбор данных (дописать)."""
    try:
        # Читаем файл асинхронно
        contents = await file.read()

        # Используем BytesIO для работы с pdfplumber
        data = BytesIO(contents)

        with pdfplumber.open(data) as pdf:
            first_page = pdf.pages[0]
            table = first_page.extract_table()

            if table is None:
                return None

            # data = table.extract()
            obj = parse_data_in_table_from_delivery(table)
            return obj

    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка при обработке PDF: {e}")
        return None

# делать проверку, сходится ли подразделение карточки service_work
# (в каком Ю находится) c подразделением в отгрузке (подсказка для "нужно ли
# перемещение?")


def clear_head_data(head: list[str], result: list = []):
    """Очищает заголовок таблицы `Задание на отгрузку` для валидации строк.

    CLEAR_ELEMENTS
    --------------
    - переносы строк;
    - пробелы;
    - дефисы.
    """
    for el in head:
        result.append(re.sub(EXTRUDE_SYMBOLS_IN_HEADER, '', el).lower())

    return result


def parse_data_in_table_from_delivery(
        objs: list[list],
        result: list[UnitOfBOMSchema] = [],
) -> Optional[list[UnitOfBOMSchema]]:
    """Валидация полезных данных и их извлечение из таблицы pdf."""

    # Извлекаем шапку таблицы и получаем её чистые заголовки:
    table_headers = clear_head_data(objs.pop(0))

    try:
        # Создать словарь с позициями нужных колонок
        positions = {
            key: table_headers.index(target_headers[key])
            for key in target_headers
            if target_headers[key] in table_headers
        }

        # Проверить, что все нужные колонки найдены
        if len(positions) != len(target_headers):
            missing = [
                target_headers[key] for key in target_headers
                if key not in positions
            ]
            raise ValueError(f'Отсутствуют колонки: {missing}')

        # Проверка, что кроме шапки в таблице есть полезные строки:
        if not len(objs):
            raise InsufficientDataError

        # Извлечь данные из строк с полезными данными:
        for row in range(len(objs)):
            row_result = {
                key: objs[row][pos].replace('\n', '')
                for key, pos in positions.items()
            }
            json_row = json.dumps(row_result)
            clear_row_result = UnitOfBOMSchema.model_validate_json(json_row)
            result.append(clear_row_result)

        return result

    except InsufficientDataError:
        print('Количество строк в таблице меньше, чем необходимо.')
        return None
    except ValidationError as e:
        print(f'Ошибка валидации: {e}')
        return None
    except IndexError as e:
        print(f'Ошибка индекса: {e}')
        return None
