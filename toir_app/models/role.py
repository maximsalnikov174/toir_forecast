from sqlalchemy import Column, String

from toir_app.core.db import Base


class Role(Base):
    """Модель ролей пользователей."""
    name = Column(String, nullable=False, unique=True)
