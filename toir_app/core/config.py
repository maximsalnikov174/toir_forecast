from typing import Optional
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс для работы с переменными окружения."""
    app_title: str = 'Приложение ТОиР'
    database_url: str  # Обязательный параметр без значения по умолчанию
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None
    superuser_name: str = 'Admin'
    superuser_surname: str = 'Adminov'
    superuser_organization: int = 1
    superuser_role: int = 1

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',  # Рекомендуется явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


# Создал глобальную переменную settings с экземпляром класса Settings, чтобы
# его можно было импортировать в любую часть приложения, где потребуется
# доступ к настройкам.
#
# Явно указал тип для переменной settings и добавил type checking коммент
settings: Settings = Settings()  # type: ignore[call-arg]

# print(settings.database_url)  # Должно показать значение из .env
