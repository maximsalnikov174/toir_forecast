from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.core.db import Base


class Role(Base):
    """Модель ролей пользователей (read_only, edit_my_organization)."""
    name = Column(String, nullable=False, unique=True)

    # Обратные связи:
    employees_by_role = relationship(
        'User',
        back_populates='users_role',
        cascade='delete'
    )
