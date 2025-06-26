from pathlib import Path
from typing import List

UPLOAD_FILE_DIR = '/dataset_from_oebs/rmt321_ATU_'
# Стандартное количество элементов в строке rmt-321:
TOTAL_VALUES_IN_RAW_RMT_321 = 22

# Процент вхождения в выборку (у нас утверждено 10%):
EXCESS_VALUE = 10

# Логирование SQL-запросов (для разработки - True)
NEED_ECHO_SQL = False

# Длины названий в моделях:
ORGANIZATION_NAME_LEN = 3  # Длина имени цеха (Ю51)
ORGANIZATION_NORMAL_NAME_LEN = 5  # 2-МГ, 3-А, 3-Л, 4-НТ, 4-УСТ, 5-НТ
CAR_MODEL_NAME_LEN = 50  # Длина названия ТС (Шевроле Нива)
STATUS_NAME_LEN = 20  # Длина названия статуса (Превышение или Подошло)
SPECIAL_STATUS_NAME_LEN = 40
SPECIAL_STATUS_FOR_CAR_COMMENT = 200
CAR_GRZ_LEN = 20  # Длина гос рег знака (У 123 АЕ 174)
SERVICE_STATUS_NAME_LEN = 40  # Длина вида обслуживания (ТО-1, ТО ГБО и тд)
STATION_NAME_LEN = 10

pattern_grz = (
    r'^([АВЕКМНОРСТУХ]{1,2})\s'
    r'(\d{3,4})\s'
    r'([АВЕКМНОРСТУХ]{0,2})\s?'
    r'([1,7][4,7]4*)'
)

pattern_grz_input_user = (
    r'^([АВЕКМНОРСТУХ]{1,2})\s?'
    r'(\d{3,4})\s?'
    r'([АВЕКМНОРСТУХ]{2})?\s?'
    r'([1,7][4,7]4*)'
)
ORGANIZATION_BASE_NAME_PATTERN = r'^Ю\d{2}$'
ORGANIZATION_NORMAL_NAME_PATTERN = r'^(\d-)?[А-Я]{1,3}$'
WORDS_AND_DIGITS = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]+$'
COMPANY_DOMAIN = r'^[a-z]+\.?[a-z]{2}@(?:atu.)?mmk.ru$'
pattern_zvr = r'^5[0-4]-АВТ-\d{7}$'
LEN_ZVR = 14
ZVR_PART_MIN = 1_000_000
ZVR_PART_MAX = 10_000_000

PATTERN_DATE_OEBS = '%d.%m.%Y %H:%M:%S'

TIMEZONE_AE = 'Asia/Yekaterinburg'

LIST_ORGANIZATIONS: list[str] = ['Ю51', 'Ю52', 'Ю53', 'Ю54']

# FIXME Уточнить, когда будут созданы все необходимые статусы:
SPECIAL_STATUS_LIST_FOR_GET_STATS: List[int] = [2, 3]

# БЛОК РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ:
# Данные для суперпользователя
ADMIN_ORGANIZATION_DATA = {'name': 'Ю80', 'normal_name': 'УПР'}
# Максимальная длина имени или фамилии сотрудника:
PERSON_FULL_NAME_LEN = 40
# Минимальная длина пароля от личного кабинета:
MIN_PASSWORD_LEN = 5
# Дефолтное время жизни (в секундах) токена для пользователя:
LIFETIME_TOKEN_IN_SECONDS = 3_600
# URL для работы с регистрацией пользователя:
ENDPOINT_URL_FOR_REGISTRATION = '/auth'
# URL для работы с аутентификацией:
ENDPOINT_URL_FOR_AUTH = f'{ENDPOINT_URL_FOR_REGISTRATION}/jwt'
# URL для получения токена для пользователя:
ENDPOINT_URL_FOR_GET_TOKEN = f'{ENDPOINT_URL_FOR_AUTH}/login'


# Настройка логгирования:
BASE_DIR = Path(__file__).parent
LOG_DIR = Path(f'{BASE_DIR}/logs')
LOG_FILE = Path(f'{LOG_DIR}/logging_toir_forecast.log')
MAX_BYTES_FOR_LOG_FILE = 10 ** 6
BACKUP_COUNT = 5
CUSTOM_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOGGER_FORMAT = '%(asctime)s | %(name)25s | %(levelname)10s || %(message)s'
