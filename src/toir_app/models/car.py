from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from constants import CAR_GRZ_LEN
from core.db import Base


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
        unique=True,
        comment='Государственный регистрационный знак',
    )
    in_archive = Column(
        Boolean,
        default=False,
        comment='Флаг нахождения в архиве (при списании/продаже)'
    )
    tg_uuid = Column(
        String(32),
        nullable=True,
        unique=True,
        default=None,
        comment='Уникальный UUID ТС',
    )
    # Связи:
    car_model_id = Column(
        Integer,
        ForeignKey('carmodel.id')
    )
    organization_id = Column(
        Integer,
        ForeignKey('organization.id')
    )
    # Обратные связи:
    car_model = relationship(
        'CarModel',
        back_populates='cars'
    )
    organization = relationship(
        'Organization',
        back_populates='cars'
    )
    service_works = relationship(
        'ServiceWork',
        back_populates='car',
        cascade='all, delete-orphan'
    )
    status_associations = relationship(
        'SpecialStatusForCar',
        back_populates='car',
        order_by='asc(SpecialStatusForCar.date_left)'  # Сортировка по дате
    )

    # def __repr__(self):
    #     return (
    #         f'{self.grz} <{self.personal_id}> - '
    #         f'{self.car_model} [{self.organization}]'
    #     )
