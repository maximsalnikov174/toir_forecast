from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from constants import PERSON_FULL_NAME_LEN
from core.db import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    name = Column(
        String(PERSON_FULL_NAME_LEN),
        nullable=False,
        comment='Имя пользователя'
    )
    surname = Column(
        String(PERSON_FULL_NAME_LEN),
        nullable=False,
        comment='Фамилия пользователя'
    )

    # Связи:
    organization_id = Column(
        Integer,
        ForeignKey('organization.id'),
        nullable=False,
        comment='Связь с подразделением через его ID.'
    )
    role_id = Column(
        Integer,
        ForeignKey('role.id'),
        nullable=False,
        comment='Связь с полномочиями через их ID.'
    )

    # Обратные связи:
    users_organization = relationship(
        'Organization',
        back_populates='employees',
        cascade='delete'
    )
    users_role = relationship(
        'Role',
        back_populates='employees_by_role',
        cascade='delete'
    )
    assigned_statuses = relationship(
        'SpecialStatusForCar',
        back_populates='user'
    )

    def __repr__(self):
        return f'{self.name} {self.surname}'
