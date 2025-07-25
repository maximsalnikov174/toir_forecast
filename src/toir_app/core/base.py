# Импортируем базовый класс Base.
from core.db import Base  # noqa
from models import (  # noqa
    Car, CarModel, Organization, ServiceName,
    ServiceStatus, ServiceStatusStats,
    ServiceWork, ServiceWorkState,
    SpecialStatus, Status, Role, User
)
