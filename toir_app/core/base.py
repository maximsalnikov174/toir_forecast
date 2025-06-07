# Импортируем базовый класс Base.
from toir_app.core.db import Base  # noqa

from toir_app.models import (  # noqa
    Car,
    CarModel,
    Organization,
    ServiceName,
    ServiceStatus,
    ServiceWork,
    SpecialStatus,
    User
)
