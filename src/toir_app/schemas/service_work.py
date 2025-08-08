from datetime import datetime as dt
from typing import Annotated, Optional, Union

from pydantic import (BaseModel, computed_field, Field, field_serializer,
                      field_validator, ValidationInfo)

from constants import (
    COMPLETED_DAYS_AGO,
    LEN_ZVR_BASE,
    PATTERN_DATE_USER_FRENDLY,
    ZVR_CREATED_DAYS_AGO,
)
from logger.logger import logger
from models import ServiceWork, Station
from schemas.station import StationBase


def convert_date_into_convenient_format(
        element,
        borderline_value,
        pattern_for_date,
        context
):
    """В зависимости от `context` формирует `дату` в удобном виде."""
    if context == 'create_update_mode':
        return element

    days_left = (dt.now()-element).days
    msg = f' -> {days_left} дней' if days_left > borderline_value else ''
    return f'{element.date().strftime(pattern_for_date)} {msg}'
    # return f'{element.strftime(pattern_for_date)} {msg}'


class ServiceWorksRequestStatus(BaseModel):
    """
    Схема записи о Сервисном Обслуживании (только ID вычисляемого статуса).
    """
    request_status_id: int


class CarAtributesInServiceWork(BaseModel):
    """
    Схема ServiceWork с полями, необходимыми для Car.

    Дополнительно - округление поля daily_distance до .1 знака.
    """
    # используется в индикаторах (нужны только 2 этих поля)
    request_reading: float
    daily_distance: float

    class Config:
        from_attributes = True

    @field_validator('daily_distance')
    def split_value(cls, value):
        """Округление суточного пробега до 1 знака после запятой."""
        return round(value, 1)


class ServiceWorkBase(CarAtributesInServiceWork):
    """
    Базовая схема записи о Сервисном Обслуживании.
    Дополнительное сравнение даты последнего сервиса и now()
    """

    car_id: int = Field(..., title='pk из таблицы Car')
    last_service_id: int = Field(..., title='pk из таблицы ServiceName')
    next_service_id: int = Field(..., title='pk из таблицы ServiceName')
    request_date: dt
    last_service_date: dt
    last_service_reading: float
    base_interval: int

    @field_validator('last_service_date')
    def last_service_date_must_be_in_past(
        cls, value: dt, info: ValidationInfo
    ) -> dt:
        """Проверка, что дата последнего сервиса - в прошлом.

        Связано с тем, что в OeBS могут сделать ошибку завершить ЗВР в будущем.
        """
        if value > info.data['request_date']:
            # # TODO ЧТО-ТО С ЭТИМ В ИТОГЕ НАДО СДЕЛАТЬ, ЧТОБ НЕ ПАДАЛ ТЕСТ
            # car_id = info.data['car_id']
            # last_service_id = info.data['last_service_id']
            # date = value.date().isoformat()

            logger.warning(
                f'📆 Дата проведения ТО ({value})- в будущем, '
                'такого быть не должно!'
                f'ТС#{info.data["car_id"]}. '
                f'Вид обслуживания #{info.data["last_service_id"]}.'
            )
            return dt(2025, 1, 1, 0, 0, 0)
        return value


class ServiceWorkWithDivergence(ServiceWorkBase):
    """Дополнительно подсчитывает отклонение пробега."""

    @computed_field
    def divergence(self) -> Optional[float]:
        """Отклонение фактического пробега от норматива (1 знак после «,»).

        Returns:
        - если значение (-) превышение
        - если значение (+) недопробег
        """
        if (
            self.request_reading
            and self.last_service_reading is not None
            and self.base_interval
        ):
            return round(
                (
                    self.last_service_reading
                    + self.base_interval
                    - self.request_reading
                ),
                1
            )
        return None


class ServiceWorkWithZVRNumber(ServiceWorkWithDivergence):
    """
    Схема записи о Сервисном Обслуживании с номером ЗВР.
    """

    id: int = Field(..., title='ID сервисного обслуживания')
    zvr_number: Optional[str] = Field(
        None,
        title='Номер ЗВР',
        description='Уникальный номер заявки на сервисное обслуживание',
    )
    zvr_create_date: Optional[dt] = Field(
        None,
        title='Дата создания ЗВР (автодата)',
        description='Дата, когда была создана заявка (ЗВР)',
    )
    service_work_completed: Optional[dt] = Field(
        None,
        title='Дата завершения работ по факту',
        description=(
            'Дата фактического завершения сервисных работ. '
            'Проставляется юзером (роль?) после выезда ТС из зоны ремонта.'
        )
    )
    request_status_id: int = Field(..., title='id расчётного статуса')
    station: Optional[StationBase] = Field(
        ...,
        title='Станция, где будут выполнены работы'
    )

    @computed_field
    def days_between_service_work_completed_and_now(self) -> Optional[int]:
        """Разница между `сегодня` и `датой фактического завершения работ`.

        Returns:
        - some days
        """
        if self.service_work_completed:
            return (dt.now()-self.service_work_completed).days
        return None

    @field_serializer('last_service_date')
    def convert_last_service_date(
        self, last_service_date: dt, info
    ) -> Union[str, dt]:
        """Обработка (отображение) поля `last_service_date`.

        ## Variants:
        - По умолчанию преобразует `datetime` в строку вида `dd.mm.yyyy` для
        отображения в главной таблице;
        - При передаче в `model_dump` параметра `context='create_update_mode'`
        значение не меняет.

        ## Special stmt:
        - в режиме `по умолчанию` выполняется проверка времени, прошедшего с
        предыдущего выполнения сервиса и, с учётом сравнения с полем
        `COMPLETED_DAYS_AGO`, может быть расширено надписью `прошло дней: ХХХ`.
        """
        return convert_date_into_convenient_format(
            element=last_service_date,
            borderline_value=COMPLETED_DAYS_AGO,
            pattern_for_date=PATTERN_DATE_USER_FRENDLY,
            context=info.context
        )

    @field_serializer('zvr_create_date')
    def convert_zvr_create_date(
        self,
        zvr_create_date: dt,
        info,
    ) -> Union[str, dt]:
        """Обработка (отображение) поля `zvr_create_date`.

        ## Variants:
        - По умолчанию преобразует `datetime` в строку вида `dd.mm.yyyy` для
        отображения в главной таблице;
        - При передаче в `model_dump` параметра `context='create_update_mode'`
        значение не меняет.

        ## Special stmt:
        - в режиме `по умолчанию` выполняется проверка времени, прошедшего с
        предыдущего выполнения сервиса и, с учётом сравнения с полем
        `ZVR_CREATED_DAYS_AGO`, может быть расширено надписью `прошло дней: Х`.
        """
        return convert_date_into_convenient_format(
            element=zvr_create_date,
            borderline_value=ZVR_CREATED_DAYS_AGO,
            pattern_for_date=PATTERN_DATE_USER_FRENDLY,
            context=info.context
        )


class ServiceWorkWithInArchive(ServiceWorkWithZVRNumber):
    """Добавлено поле состояния (в архиве или нет)"""

    in_archive: bool


class AddZvrSchema(BaseModel):
    """Проверка атрибутов для добавления `№ ЗВР` к карточке `ServiceWork`."""

    service_work_id: Annotated[int, ServiceWork.id]
    zvr_number: str = Field(
        ..., min_length=LEN_ZVR_BASE, max_length=LEN_ZVR_BASE,
    )
    station_id: Annotated[int, Station.id]
