# Процент вхождения в выборку (у нас утверждено 10%):
EXCESS_VALUE = 10

# Длины названий в моделях:
ORGANIZATION_NAME_LEN = 3  # Длина имени цеха (Ю51)
ORGANIZATION_NORMAL_NAME_LEN = 5  # 2-МГ, 3-А, 3-Л, 4-НТ, 4-УСТ, 5-НТ
CAR_MODEL_NAME_LEN = 50  # Длина названия ТС (Шевроле Нива)
STATUS_NAME_LEN = 20  # Длина названия статуса (Превышение или Подошло)
SPECIAL_STATUS_NAME_LEN = 40
CAR_GRZ_LEN = 20  # Длина гос рег знака (У 123 АЕ 174)
SERVICE_STATUS_NAME_LEN = 40  # Длина вида обслуживания (ТО-1, ТО ГБО и тд)
PERSON_FULL_NAME_LEN = 40


pattern_grz = (
    r'^([АВЕКМНОРСТУХ]{1,2})\s'
    r'(\d{3,4})\s'
    r'([АВЕКМНОРСТУХ]{0,2})\s?'
    r'([[1,7][4,7]4*)'
)

pattern_grz_input_user = (
    r'^([АВЕКМНОРСТУХ]{1,2})\s?'
    r'(\d{3,4})\s?'
    r'([АВЕКМНОРСТУХ]{2})?\s?'
    r'([[1,7][4,7]4*)'
)

pattern_zvr = r'^5[0-4]-АВТ-\d{7}$'
LEN_ZVR = 14
