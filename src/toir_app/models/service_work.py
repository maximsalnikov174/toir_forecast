from calendar import monthrange
from datetime import datetime as dt

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from constants import EXCESS_VALUE, LEN_ZVR_TOTAL
from core.db import Base
from logger.logger import logger
from models import Status
from schemas.convertation import BaseCarData


class ServiceWork(Base):
    """
    Модель сервисного обслуживания.
    """
    last_service_date = Column(
        DateTime,
        nullable=False,
        comment='Дата последнего обслуживания'
    )
    last_service_reading = Column(
        Float,
        nullable=False,
        comment='Пробег при последнем обслуживании'
    )
    request_date = Column(
        DateTime,
        nullable=False,
        comment='Дата запроса (получение файла csv)'
    )
    request_reading = Column(
        Float,
        nullable=False,
        comment='Показания на дату запроса (получение файла csv)'
    )

    base_interval = Column(
        Float,
        nullable=False,
        comment='Базовый интервал обслуживания (получение csv)'
    )
    daily_distance = Column(
        Float,
        nullable=False,
        comment='Среднесуточный пробег (получение csv)'
    )
    zvr_number = Column(
        'zrv_number',
        String(LEN_ZVR_TOTAL),
        nullable=True,
        unique=True,
        comment='ЗВР для данной работы'
    )
    zvr_create_date = Column(
        DateTime,
        default=None,
        comment='Дата создания ЗВР'
    )
    service_work_completed = Column(
        DateTime,
        default=None,
        comment='Дата фактического завершения работ (но ЗВР пока не закрыт)'
    )
    in_archive = Column(
        Boolean,
        default=False,
        comment='Автоматический перевод записи в архив'
    )
    # Связи с другими таблицами:
    car_id = Column(
        Integer,
        ForeignKey('car.id'),
        nullable=False
    )
    last_service_id = Column(
        Integer,
        ForeignKey('servicename.id')
    )
    next_service_id = Column(
        Integer,
        ForeignKey('servicename.id')
    )
    station_id = Column(
        Integer,
        ForeignKey('station.id', name='fk_service_work_station_id_station'),
        nullable=True,
        default=None
    )
    # Вычисляемое поле статуса (превыш/подошло/не надо) по собранным данным:
    request_status_id = Column(
        Integer,
        ForeignKey('servicestatus.id')
    )
    # Обратные связи:
    car = relationship(
        'Car',
        back_populates='service_works'
    )
    last_service = relationship(
        'ServiceName',
        foreign_keys=[last_service_id],
        back_populates='completed_works'
    )
    next_service = relationship(
        'ServiceName',
        foreign_keys=[next_service_id],
        back_populates='current_works'
    )
    request_status = relationship(
        'ServiceStatus',
        back_populates='all_services',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='delete',
        doc='М:1 Список работ (записей) в данном сервисном статусе.'
    )
    station = relationship(
        'Station',
        back_populates='station_works'
    )

    @property
    def calculated_status(self) -> Status:
        """
        Определяет статус с учётом принимаемых параметров из csv.

        Returns:
            Status: Текущий статус обслуживания

        Examples:
            - Превышение
            - Подошло
        """
        element = {
            'base_interval': self.base_interval,
            'daily_distance': self.daily_distance,
            'dt_now': self.request_date,
            'last_service_reading': self.last_service_reading,
            'reading_now': self.request_reading
        }

        try:
            validated_data = BaseCarData.model_validate(element)
            return self._calculated_status(validated_data)
        except Exception as e:
            logger.error(f'Ошибка расчета статуса: {e}')
            return Status.BAD_REQUEST  # Возвращаем статус с ошибкой

    def _calculated_status(self, data: BaseCarData) -> Status:
        """
        Рассчитывает статус работы для принятия решения.

        Returns:
            Возвращает Status.value

        Examples:
            - Превышение
            - Подошло
        """

        # Диапазон превышения пробега (экспертно, границы захвата данных):
        exceed_value = round(data.base_interval * EXCESS_VALUE / 100, 1)

        # Пробег (показания одометра) для проведения следующего обслуживания:
        next_service_reading = (
            data.last_service_reading + float(data.base_interval)
        )

        # Ожидаемый пробег к концу текущего месяца:
        expected_reading_at_the_months_end = (
            self._predict_reading_when_current_month_left(
                data.dt_now, data.daily_distance, data.reading_now
            )
        )

        # Считаем отклонение от планового сервиса:
        delta = data.reading_now - next_service_reading

        if delta >= exceed_value:
            return Status.DANGER
        elif abs(delta) < exceed_value:
            return Status.TIME_HAS_COME
        elif expected_reading_at_the_months_end >= next_service_reading:
            return Status.WAIT_MOMENT
        else:
            return Status.NO_NEED

    def _predict_reading_when_current_month_left(
        self,
        current_date: dt,
        daily_distance: float,
        reading_now: float
    ) -> float:
        """
        Расчитывает ожидаемый пробег на конец месяца с учётом ср.сут пробега.

        Необходим для определения наступления события в текущем месяце.

        Returns:
        - величину пробега (км) на последний день месяца.
        """
        # Дней в текущем месяце:
        days_in_month = monthrange(current_date.year, current_date.month)[1]

        # Дней осталось:
        days_left = days_in_month - current_date.day

        forecast_reading = days_left * daily_distance + 1  # ожидаемый пробег
        return forecast_reading + reading_now

    def _calculate_divergence(self):
        """
        Расчитывает отклонение фактического пробега до требуемого для сервиса.

        Returns:
        - если значение (-) -> превышение
        - если значение (+) -> недопробег
        """
        if (
            self.request_reading
            and self.last_service_reading
            and self.base_interval
        ):
            return (
                self.last_service_reading
                + self.base_interval
                - self.request_reading
            )
        return None
