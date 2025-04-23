from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from toir_app.constants import CAR_GRZ_LEN
from toir_app.core.db import Base


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
        'CarModel',
        back_populates='cars'
    )

    organization_id = Column(
        Integer,
        ForeignKey('organization.id')
    )
    organization = relationship(
        'Organization',
        back_populates='cars'
    )

    special_status_id = Column(
        Integer,
        ForeignKey('specialstatus.id'),
        nullable=True
    )
    special_status = relationship(
        'SpecialStatus',
        back_populates='cars'
    )

    service_works = relationship(
        'ServiceWork',
        back_populates='car',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return (
            f'{self.grz} <{self.personal_id}> - '
            f'{self.car_model} [{self.organization}]'
        )
