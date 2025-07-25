from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс для работы с переменными окружения."""
    app_title: str = 'Приложение ТОиР'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None
    superuser_name: str = 'Admin'
    superuser_surname: str = 'Adminov'
    superuser_organization: int = 1
    superuser_role: int = 1
    date_in_data: str = '2024_12_31'
    upload_data_from_csv: bool = False
    db_in_pg: bool = False
    postgres_db: str = 'toir_db'
    postgres_user: str = 'user'
    postgres_password: str = 'password'
    db_host: str = 'db_host'
    db_port: int = 5432

    @property
    def database_url(self) -> str:
        """Формирует строку подключения к базе данных."""
        if self.db_in_pg is True:
            return (
                f'postgresql+asyncpg://'
                f'{self.postgres_user}:{self.postgres_password}'
                f'@{self.db_host}:{self.db_port}/{self.postgres_db}'
            )
        return 'sqlite+aiosqlite:///./fast_toir.db'

    model_config = SettingsConfigDict(
        env_file='infra/.env',
        env_file_encoding='utf-8',  # Рекомендуется явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


# Глобальная переменная settings с экземпляром класса Settings, чтобы
# его можно было импортировать в любую часть приложения, где потребуется
# доступ к настройкам:

settings: Settings = Settings()
