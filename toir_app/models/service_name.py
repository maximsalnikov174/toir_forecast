from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.constants import SERVICE_STATUS_NAME_LEN
from toir_app.core.db import Base


class ServiceName(Base):
    """
    Модель видов технического обслуживания.

    Примеры:
    - ТО-1
    - ТО-2
    - ЗМ ДВС
    - ТО ГБО
    """
    name = Column(
        String(SERVICE_STATUS_NAME_LEN),
        nullable=False,
        unique=True
    )

    # Связи с другими таблицами:
    completed_works = relationship(
        'ServiceWork',
        foreign_keys='[ServiceWork.last_service_id]',
        back_populates='last_service',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='delete',
        doc='предыдущая работа.'
    )
    current_works = relationship(
        'ServiceWork',
        foreign_keys='[ServiceWork.next_service_id]',
        back_populates='next_service',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='delete',
        doc='предстоящая работа.'
    )

    def __repr__(self):
        return f'<{self.name}>'
