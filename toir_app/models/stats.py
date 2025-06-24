from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from toir_app.core.db import Base


class ServiceWorkState(Base):
    """Модель сбора статистики по состояниям service_work."""
    with_open_zvr = Column(
        Integer,
        nullable=False,
        comment='В состоянии с открытым ЗВР'
    )
    de_facto_completed = Column(
        Integer,
        nullable=False,
        comment='В состоянии фактического завершения'
    )
    without_zvr = Column(
        Integer,
        nullable=False,
        comment='В состоянии без ЗВР'
    )


class ServiceStatusStats(Base):
    """Модель сбора статистики по сервисным статусам в различных состояниях."""
    stats_date = Column(
        DateTime,
        nullable=False,
        comment='Дата сбора данных (после обработки файла csv)'
    )
    organization_id = Column(
        Integer,
        ForeignKey('organization.id'),
        nullable=False
    )
    danger_slice_id = Column(
        Integer,
        ForeignKey('serviceworkstate.id'),
        unique=True,
        nullable=False
    )
    time_has_come_slice_id = Column(
        Integer,
        ForeignKey('serviceworkstate.id'),
        unique=True,
        nullable=False
    )
    wait_moment_slice_id = Column(
        Integer,
        ForeignKey('serviceworkstate.id'),
        unique=True,
        nullable=False
    )
    no_need_slice_id = Column(
        Integer,
        ForeignKey('serviceworkstate.id'),
        unique=True,
        nullable=False
    )
    bad_request_slice_id = Column(
        Integer,
        ForeignKey('serviceworkstate.id'),
        unique=True,
        nullable=False
    )

    # Обратные связи:
    organization = relationship(
        'Organization',
        back_populates='stats'
    )
    danger_slice = relationship(
        'serviceworkstate',
        foreign_keys=[danger_slice_id],
        backref="danger_status_stats"
    )
    time_has_come_slice = relationship(
        'serviceworkstate',
        foreign_keys=[time_has_come_slice_id],
        backref="time_has_come_status_stats"
    )
    wait_moment_slice = relationship(
        'serviceworkstate',
        foreign_keys=[wait_moment_slice_id],
        backref="wait_moment_status_stats"
    )
    no_need_slice = relationship(
        'serviceworkstate',
        foreign_keys=[no_need_slice_id],
        backref="no_need_status_stats"
    )
    bad_request_slice = relationship(
        'serviceworkstate',
        foreign_keys=[bad_request_slice_id],
        backref="bad_request_status_stats"
    )
