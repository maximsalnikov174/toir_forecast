import json
import re
from io import BytesIO
from typing import Optional

import pdfplumber
from pdfplumber.page import Page
from fastapi import UploadFile
from pydantic import ValidationError

from core.config import settings
from constants import BAR_CODE_PATTERN, EXTRUDE_SYMBOLS_IN_HEADER
from exception import (
    BadTypeUploadFileException,
    BarcodeInAreaNotFoundException,
    BarcodeNotValidException,
    InsufficientDataError,
    ObjectIsExistException,
)
from schemas.unit_of_bom import BOMDocs as BOMDocsSchema
from schemas.unit_of_bom import RawUnitOfBOM, RawUnitOfBOMWithBarcode
from schemas.unit_of_bom import UnitOfBOM as UnitOfBOMSchema

target_headers = {
    'delivery': 'номердоставки',
    'snb': 'номенклатурныйномер',
    'material_name': 'наименование',
    'material_count': 'колвозапрошено',
    'from_organization': 'организацияполучатель',
}


# TODO переделать это все на классы:

def get_barcode(page: Page) -> str:
    """Извлекает идентификатор штрих-кода из документа."""
    bar_code_area = page.within_bbox(bbox=settings.get_barcode_area)
    bar_code_value = bar_code_area.extract_text().replace(' ', '')
    if bar_code_value is None:
        raise BarcodeInAreaNotFoundException
    result = re.match(BAR_CODE_PATTERN, bar_code_value)
    if not result:
        raise BarcodeNotValidException
    return result.group()


async def get_payload_data_in_pdf_file(
        file: UploadFile,
) -> Optional[RawUnitOfBOMWithBarcode]:
    """Сбор данных (дописать)."""
    try:
        # Читаем файл асинхронно
        if file.content_type != 'application/pdf':
            raise BadTypeUploadFileException

        contents = await file.read()

        # Используем BytesIO для работы с pdfplumber
        data = BytesIO(contents)

        with pdfplumber.open(data) as pdf:
            first_page = pdf.pages[0]

            bar_code = get_barcode(first_page)

            table = first_page.extract_table()

            if table is None or bar_code is None:
                return None

            table_payload = parse_data_in_table_from_delivery(objs=table)

            result = RawUnitOfBOMWithBarcode(
                unit_of_bom_list=table_payload.unit_of_bom_list,
                unit_of_bom_doc=table_payload.unit_of_bom_doc,
                bar_code=bar_code
            )

            return result

    except BadTypeUploadFileException:
        # print('Тип файла - не pdf')
        return None
    except ValidationError as e:
        print(f'Ошибка валидации: {e}')
        return None
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
        objs: list[list]
) -> Optional[RawUnitOfBOM]:
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

        doc_result: set[BOMDocsSchema] = set()
        unit_of_bom_result: list[UnitOfBOMSchema] = list()

        # Извлечь данные из строк с полезными данными:
        for row in range(len(objs)):
            row_result = {
                key: objs[row][pos].replace('\n', '')
                for key, pos in positions.items()
            }
            json_row = json.dumps(row_result)

            clear_bom_docs = BOMDocsSchema.model_validate_json(json_row)
            clear_row_result = UnitOfBOMSchema.model_validate_json(json_row)

            # Проверяю уникальность общей части данных:
            doc_result.add(tuple(clear_bom_docs.model_dump().values()))

            unit_of_bom_result.append(clear_row_result)

        if len(doc_result) != 1:
            raise ObjectIsExistException  # выбросить исключение, что данные не уникальны

        result = RawUnitOfBOM(
            unit_of_bom_doc=clear_bom_docs,
            unit_of_bom_list=unit_of_bom_result
        )

        return result

    except InsufficientDataError:
        print('Количество строк в таблице меньше, чем необходимо.')
        return None
    except ObjectIsExistException:
        print('Переданные данные не уникальны, проверьте исходники.')
        return None
    except ValidationError as e:
        print(f'Ошибка валидации: {e}')
        return None
    except IndexError as e:
        print(f'Ошибка индекса: {e}')
        return None
