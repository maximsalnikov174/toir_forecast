from datetime import datetime as dt
from calendar import monthrange

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import EXCESS_VALUE
from toir_app.core.db import Base
# from toir_app.models.car import Car
# from toir_app.models.service_name import ServiceName
from toir_app.models.service_status import ServiceStatus
from toir_app.models.static_model import Status
from toir_app.schemas.convertation import BaseCarData


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
        # if other_dict:
        #     element = {
        #         'base_interval': other_dict['base_interval'],
        #         'daily_distance': other_dict['daily_distance'],
        #         'dt_now': other_dict['request_date'],
        #         'last_service_reading': other_dict['last_service_reading'],
        #         'reading_now': other_dict['request_reading']
        #     }
        # else:
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
            print(f'Ошибка расчета статуса: {e}')
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

    async def update_request_status(self, session: AsyncSession):
        """
        Обновляет request_status на основе вычисленного статуса.
        """
        current_status_now = self.request_status_id
        calculate_status = self.calculated_status
        new_status = await session.scalar(
            select(ServiceStatus).where(
                ServiceStatus.name == calculate_status.value
            )
        )

        # TODO добавить еще проверку сравнения записанного с обновленным

        if calculate_status != current_status_now:  # проверить эту строчку
            self.request_status = new_status
            self.request_status_id = new_status.id
        # TODO если не удалось получить new_status - нужна будет обработка
        # else:
        #     ...

        return self
