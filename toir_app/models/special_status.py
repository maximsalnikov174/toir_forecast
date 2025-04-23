from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.constants import SPECIAL_STATUS_NAME_LEN
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
    cars = relationship(
        'Car',
        back_populates='special_status',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей в данной категории.'
    )

    def __repr__(self):
        return f'<{self.name}>'
