# Импортируем базовый класс Base.
from toir_app.core.db import Base  # noqa
from toir_app.models import (Car, CarModel, Organization, ServiceName,  # noqa
                             ServiceStatus, ServiceStatusStats,  # noqa
                             ServiceWork, ServiceWorkState,  # noqa
                             SpecialStatus, Status, Role, User)  # noqa
