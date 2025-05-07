from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.constants import STATUS_NAME_LEN
from toir_app.core.db import Base


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
        back_populates='request_status',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='delete',
        doc='1:M Список работ (записей) в данном сервисном статусе.'
    )

    def __repr__(self):
        return f'<{self.name}>'
