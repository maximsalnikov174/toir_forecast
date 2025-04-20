from sqlalchemy import (Boolean,
                        Column,
                        DateTime,
                        Float,
                        ForeignKey,
                        Integer,
                        String)
from sqlalchemy.orm import relationship  # , declared_attr

from toir_app.constants import (CAR_GRZ_LEN,
                                CAR_MODEL_NAME_LEN,
                                EXCESS_VALUE,
                                ORGANIZATION_NAME_LEN,
                                ORGANIZATION_NORMAL_NAME_LEN,
                                SERVICE_STATUS_NAME_LEN,
                                SPECIAL_STATUS_NAME_LEN,
                                STATUS_NAME_LEN)
from toir_app.core.db import Base
from toir_app.function import predict_reading_when_current_month_left
from toir_app.schemas.schemas import BaseCarData, Status


class Role(Base):
    """Модель ролей пользователей."""
    pass


class Organization(Base):
    """
    Модель Цеха.

    Example:
    - Цех Ю51 (2-МГ)
    """
    name = Column(
        String(ORGANIZATION_NAME_LEN),
        nullable=False,
        unique=True,
        comment='Название подразделения в формате Ю51'
    )
    normal_name = Column(
        String(ORGANIZATION_NORMAL_NAME_LEN),
        nullable=True,  # заглушка на этапе создания
        comment='Название цеха в привычном формате'
    )

    cars = relationship(
        'Car',
        back_populates='organization',  # явное определение отношений
        lazy='selectin',
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей, числящихся в данном цехе.'
    )

    def __repr__(self):
        return f'<Цех {self.name}>'


class CarModel(Base):
    """
    Модель Марок Автомобилей.

    Example:
    - Модель Шевроле Нива
    """
    name = Column(
        String(CAR_MODEL_NAME_LEN),
        nullable=False,
        unique=True,
        comment='Бренд + модификация Автомобиля'
    )

    cars = relationship(
        'Car',
        back_populates='car_model',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей данной Марки.'
    )

    def __repr__(self):
        return f'<Модель {self.name}>'


class ServiceStatus(Base):
    """
    Модель присваиваемых Статусов для каждой полученной записи.

    Примеры статусов:
    - Превышение
    - Подошло
    - Ожидается
    - Нет необходимости
    """
    name = Column(
        String(STATUS_NAME_LEN),
        nullable=False,
        unique=True,
        comment='Рассчётный статус для каждой записи из OeBS'
    )

    all_services = relationship(
        'ServiceWork',
        back_populates='service_status',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список работ (записей) в данном сервисном статусе.'
    )

    def __repr__(self):
        return f'<{self.name}>'


class SpecialStatus(Base):
    """
    Модель глобальных статус (для админа).

    Этими статусами можно установить особое состояние для ТС.

    Примеры:
    - на ВР
    - к выбытию
    - на реализации
    """
    name = Column(
        String(SPECIAL_STATUS_NAME_LEN),
        nullable=False,
        unique=True
    )
    cars = relationship(
        'Car',
        back_populates='special_status',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей в данной категории.'
    )

    def __repr__(self):
        return f'<{self.name}>'


class ServiceName(Base):
    """
    Модель видов технического обслуживания.

    Примеры:
    - ТО-1
    - ТО-2
    - ЗМ ДВС
    - ТО ГБО
    """
    name = Column(
        String(SERVICE_STATUS_NAME_LEN),
        nullable=False,
        unique=True
    )
    cars = relationship(
        'Car',
        back_populates='service_name',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей с данным видом техобслуживания.'
    )

    def __repr__(self):
        return f'<{self.name}>'


class Car(Base):
    """
    Базовое описание Транспортного средства.
    """
    personal_id = Column(
        Integer,
        unique=True,
        nullable=False,
        comment='Уникальный ID из OeBS'
    )
    grz = Column(
        String(CAR_GRZ_LEN),
        nullable=False,
        comment='Государственный регистрационный знак'
    )
    in_archive = Column(
        Boolean,
        default=False,
        comment='Флаг нахождения в архиве'
    )

    # Связи (FIXME не уверен, что back_populates='car' для всех == правильно):
    car_model_id = Column(
        Integer,
        ForeignKey('carmodel.id'),
        nullable=False
    )
    car_model = relationship(
        CarModel,
        back_populates='car'  # или cars
    )

    organization_id = Column(
        Integer,
        ForeignKey('organization.id')
    )
    organization = relationship(
        Organization,
        back_populates='car'  # или cars
    )

    special_status_id = Column(
        Integer,
        ForeignKey('specialstatus.id'),
        nullable=True
    )
    special_status = relationship(
        'SpecialStatus',
        back_populates='car'
    )

    def __repr__(self):
        return (
            f'{self.grz} <{self.personal_id}> - '
            f'{self.car_model} [{self.organization}]'
        )


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
    # # ТС:
    car_id = Column(
        Integer,
        ForeignKey('car.id'),
        nullable=False
    )
    car = relationship(
        Car,
        back_populates='service_works'
    )

    # # Прошлый вид обслуживания:
    last_service_id = Column(
        Integer,
        ForeignKey('servicename.id')
    )
    last_service = relationship(
        ServiceName,
        foreign_keys=[last_service_id]  # ???
    )

    # # Предстоящий вид обслуживания:
    next_service_id = Column(
        Integer,
        ForeignKey('servicename.id')
    )
    next_service = relationship(
        ServiceName,
        foreign_keys=[next_service_id]  # ???
    )

    # # Вычисляемое поле статуса (превыш/подошло/не надо) по собранным данным:
    request_status_id = Column(
        Integer,
        ForeignKey('servicestatus.id')
    )
    request_status = relationship(
        ServiceStatus,
        back_populates='service_status',
        lazy='selectin',  # более эффективная загрузка связей
        # cascade='all, delete-orphan',
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
        element = {
            'base_interval': self.base_interval,
            'daily_distance': self.daily_distance,
            'dt_now': self.request_date,
            'last_service_reading': self.last_service_reading,
            'reading_now': self.request_reading
        }

        try:
            validated_data = BaseCarData.model_validate(element)
            return self._calculate_service_status(validated_data)
        except Exception as e:
            print(f'Ошибка расчета статуса: {e}')
            return Status.BAD_REQUEST  # Возвращаем статус с ошибкой

    def _calculated_status(self, data: BaseCarData) -> Status:
        """
        (Внутренний метод) Рассчитывает статус работы для принятия решения.

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
            predict_reading_when_current_month_left(
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

    def update_request_status(self):
        """Обновляет request_status на основе вычисленного статуса

        Метод на перспективу, пока не надо его задействовать.
        Как-будто его вообще надо расширить для бОльшего количества полей.
        """
        current_status = self.calculated_status
        new_status = (
            ServiceStatus.query.filter_by(name=current_status.value).first()
        )

        # Обновляем только отношение (без id):
        if new_status:
            self.request_status = new_status
