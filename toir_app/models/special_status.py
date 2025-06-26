from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from toir_app.constants import (SPECIAL_STATUS_FOR_CAR_COMMENT,
                                SPECIAL_STATUS_NAME_LEN)
from toir_app.core.db import Base


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
    car_associations = relationship(
        'SpecialStatusForCar',
        back_populates='special_status'
    )

    def __repr__(self):
        return f'<{self.name}>'


class SpecialStatusForCar(Base):

    # # нельзя для одной машины поставить несколько раз одинаковый статус
    # # т.е. набор машина-статус-время_не_прошло должны быть уникальны
    # __table_args__ = (
    #    UniqueConstraint(
    #        'car_id',
    #        'special_status_id',
    #        name='uq_special_status_for_car'
    #     ),
    # )

    date_left = Column(Date, nullable=False)
    comment = Column(
        String(SPECIAL_STATUS_FOR_CAR_COMMENT),
        nullable=True,
        default=None
    )
    is_active = Column(
        Boolean,
        default=True,
        comment='Актуальность статуса для ТС'
    )
    # Связи с другими таблицами:
    car_id = Column(
        Integer,
        ForeignKey('car.id'),
        primary_key=True
    )
    special_status_id = Column(
        Integer,
        ForeignKey('specialstatus.id'),
        primary_key=True
    )
    assigned_by_user_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
    )
    # Обратные связи:
    car = relationship('Car', back_populates='status_associations')
    special_status = relationship(
        'SpecialStatus', back_populates='car_associations'
    )
    user = relationship('User', back_populates='assigned_statuses')
