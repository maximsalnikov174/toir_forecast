from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from toir_app.constants import STATION_NAME_LEN
from toir_app.core.db import Base


class Station(Base):
    """
    Модель Сервисной зоны.

    Example:
    - УРГА, УРЛА, Сторона
    """
    name = Column(
        String(STATION_NAME_LEN),
        nullable=False,
        unique=True,
        comment='Название зоны сервиса'
    )
    # Обратные связи:
    station_works = relationship(
        'ServiceWork',
        back_populates='station',
        cascade='delete'
    )

    def __repr__(self):
        return f'<Цех {self.name}>'
