from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from core.db import Base


class Role(Base):
    """Модель ролей пользователей (read_only, edit_my_organization)."""
    name = Column(String, nullable=False, unique=True)

    # Обратные связи:
    employees_by_role = relationship(
        'User',
        back_populates='users_role',
        cascade='delete'
    )
    # Связь многие-ко-многим с SpecialStatus
    allowed_special_statuses = relationship(
        'SpecialStatus',
        secondary='special_status_role_association',
        back_populates='allowed_roles'
    )
