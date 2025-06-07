from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from toir_app.core.db import Base
from toir_app.constants import PERSON_FULL_NAME_LEN


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
    organization = relationship(
        'Organization',
        back_populates='employees',
        cascade='delete'
    )
    role = relationship(
        'Role',
        back_populates='employees_by_role',
        cascade='delete'
    )

    def __repr__(self):
        return f'{self.name} {self.surname} ({self.organization.name})'
