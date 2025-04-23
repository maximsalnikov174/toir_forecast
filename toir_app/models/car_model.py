from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.constants import CAR_MODEL_NAME_LEN
from toir_app.core.db import Base


class CarModel(Base):
    """
    Модель Марок Автомобилей.

    Example:
    - Модель Шевроле Нива
    """
    name = Column(
        String(CAR_MODEL_NAME_LEN),
        nullable=False,
        unique=True,
        comment='Бренд + модификация Автомобиля'
    )

    cars = relationship(
        'Car',
        back_populates='car_model',
        lazy='selectin',  # более эффективная загрузка связей
        cascade='all, delete-orphan',
        doc='1:M Список автомобилей данной Марки.'
    )

    def __repr__(self):
        return f'<Модель {self.name}>'
