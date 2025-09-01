# РАБОТА С РЕГУЛЯРНЫМИ ВЫРАЖЕНИЯМИ ДЛЯ ОБРАБОТКИ ВИДОВ РАБОТ (SERVICE_NAME):

import re
from collections import defaultdict
from enum import Enum
from typing import DefaultDict, Dict, List, Optional, Pattern

from exception import ServiceNameNotFoundException, ServiceNameBadDataException

# Объявляем типы:
ServiceNameMapping = Dict[str, List[str]]  # {нормализованное: [варианты]}
ReverseServiceMapping = DefaultDict[str, str]  # {вариант: нормализованное}


class UsersServiceName(str, Enum):
    """Приведенные виды технического обслуживания (общий список).

    ## Detail:
    - работы выстроены по приоритету от самых важных/частых к специфическим.
    """
    TO_4 = 'ТО-4'
    TO_2 = 'ТО-2'
    TO = 'ТО'
    TO_1 = 'ТО-1'
    TO_2000 = 'ТО-2000'
    TO_1000 = 'ТО-1000'
    TO_500 = 'ТО-500'
    TO_250 = 'ТО-250'
    TO_GAZ = 'ТО ГБО'
    ENGINE = 'Замена масла ДВС'
    GEARBOX = 'Замена масла КПП'
    ANTIFREEZE = 'Замена антифриза'
    HYDRO = 'Замена гидромасла'
    DRIVE_AXLE = 'Замена масла ведущего моста'
    STEERING_WHEEL = 'Замена масла редуктора РУ'
    BRAKE_FLUID = 'Замена тормозной жидкости'
    ON_BOARD_TRANSMISSION = 'Замена масла в бортовой передаче'


# СЛОВАРЬ ЗНАЧЕНИЙ ВИДОВ РАБОТ ИЗ OEBS, КОТОРЫЙ НУЖНО ПРИВЕСТИ К ЕДИНОМУ ВИДУ:
#
# По ходу развития системы OeBS (в основном за счет появления новой техники)
# потребуется расширять данный конвертер и обрабатывать "новые" придуманные
# названия видов работ.


convert_service_name: ServiceNameMapping = {
    UsersServiceName.ANTIFREEZE.value: [
        'ЗамАнтифриза',
        'ЗамОхлаждающейЖидкости'
    ],
    UsersServiceName.HYDRO.value: [
        'ЗамГидроМасла'
    ],
    UsersServiceName.DRIVE_AXLE.value: [
        'ЗамМаслаВедущегоМоста',
        'ЗамМаслаВедущегоМоста'
    ],
    UsersServiceName.ENGINE.value: [
        'ЗамМаслаДВС',
        'ЗамМаслДВС',
        'ЗМ',
        'ЗамМасла ДВС'
    ],
    UsersServiceName.GEARBOX.value: [
        'ЗамМаслаКПП',
        'ЗамМаслаТрансмиссии',
        'ЗамМаслаКППZF'
    ],
    UsersServiceName.STEERING_WHEEL.value: [
        'ЗамМаслаРедукторРУ'
    ],
    UsersServiceName.BRAKE_FLUID.value: [
        'ЗамТормознойЖидкости'
    ],
    UsersServiceName.ON_BOARD_TRANSMISSION.value: [
        'ЗамМаслаБортовойПередачи',
        'ЗамМаслаБортПередачи'
    ],
    UsersServiceName.TO_2000.value: [
        'ТО-2000'
    ],
    UsersServiceName.TO_500.value: [
        'ТО-500'
    ],
    UsersServiceName.TO_250.value: [
        'ТО-250'
    ],
    UsersServiceName.TO_2.value: [
        'ТО-2'
    ],
    UsersServiceName.TO_4.value: [
        'ТО-4'
    ],
    UsersServiceName.TO_1000.value: [
        'ТО-1000'
    ],
    UsersServiceName.TO_1.value: [
        'ТО-1',
        'ТО-1 (смазка)',
        'РП (смазка)',
        'РП'
    ],
    UsersServiceName.TO_GAZ.value: [
        'ТО ГБО'
    ],
    UsersServiceName.TO.value: [
        'ТО'
    ]
}


# Создаем обратный словарь для замены {вариант: нормализованное_название}
reverse_mapping: ReverseServiceMapping = defaultdict(str)
for normalized, variants in convert_service_name.items():
    for variant in variants:
        reverse_mapping[variant] = normalized


# Определение вида работ:

# ------------------------------ПАТТЕРНЫ------------------------------

# Группы с исключительными названиями в заголовке:
pattern_exception_one = r'^(ЗамМасла ДВС)'
pattern_exception_two = r'^(РП) \(смазка\)'
pattern_exception_three = r'^(ТО ГБО)'
pattern_exception_four = r'^(ТО-\d{1,4})'

# Группа для работ с «:» (самое популярное):
pattern_with_spec_symbol = r'^(\S+?)[\s|:]'

# Группа для работ с первым словом:
pattern_one_word = r'^(\S+?)[\s]'

patterns = [
    pattern_exception_one,
    pattern_exception_two,
    pattern_exception_three,
    pattern_exception_four,
    pattern_with_spec_symbol,
    pattern_one_word
]

# Компилируем паттерны отдельно
all_patterns: List[Pattern[str]] = (
    [re.compile(pattern) for pattern in patterns]
)


# -------------------------ПРОВЕРКА СООТВЕТСТВИЯ-------------------------

async def normalize_service_name(service_name: str) -> Optional[str]:
    """
    Нормализует название услуги по словарю замен.

    ARGS
    ----
    service_name: Входное название услуги

    RETURNS:
    --------
    - Нормализованное название
    - None, если:
    не найдено соответствие паттернам;
    нет соответствия в словаре замен.
    """
    # Если подали не строку:
    if not isinstance(service_name, str):
        raise ServiceNameBadDataException

    # Если строка пустая:
    if not (cleaned_name := service_name.strip()):
        return ServiceNameBadDataException

    for pattern in all_patterns:
        if (match := pattern.match(cleaned_name)):
            matched_text = match.group(1)
            final_text = reverse_mapping.get(matched_text)
            if final_text:
                return final_text

    raise ServiceNameNotFoundException(reason=cleaned_name)
