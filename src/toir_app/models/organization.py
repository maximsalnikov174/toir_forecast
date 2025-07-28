from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from constants import (
    ORGANIZATION_NAME_LEN,
    ORGANIZATION_NORMAL_NAME_LEN,
)
from core.db import Base


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
        comment='Название цеха в привычном формате.'
    )

    cars = relationship(
        'Car',
        back_populates='organization',  # явное определение отношений
        lazy='selectin',
        cascade='delete',
        doc='1:M Список автомобилей, числящихся в данном цехе.'
    )
    employees = relationship(
        'User',
        back_populates='users_organization',
        cascade='delete'
    )
    stats = relationship(
        'ServiceStatusStats',
        back_populates='organization',
        cascade='delete'
    )

    def __repr__(self):
        return f'<Цех {self.name}>'
