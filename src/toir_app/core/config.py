from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants import ENCODING_DEFAULT


class Settings(BaseSettings):
    """Класс для работы с переменными окружения."""
    app_title: str = 'Приложение ТОиР'
    for_local: bool = False  # для локальной разработки
    cors_on_frontend: bool = True  # для подключения фронтенда
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None
    superuser_name: str = 'Admin'
    superuser_surname: str = 'Adminov'
    superuser_organization: int = 1
    superuser_role: int = 1
    db_in_pg: bool = False
    postgres_db: str = 'toir_db'
    postgres_user: str = 'user'
    postgres_password: str = 'password'
    db_host: str = 'db_host'
    db_port: int = 5432
    admin_tg_id: int = 1
    chat_id: int = 1
    tg_bot_token: str = 'some_token'

    # # настройка minIO (пока не нужно)
    # minio_endpoint: str = 'minio:9000'
    # minio_bucket: str = 'sw_docs'
    # minio_secure: bool = False
    # minio_access_key: Optional[str] = None
    # minio_secret_key: Optional[str] = None

    # настройки для PDF-файла «задания на отгрузку»:
    coord_x1: int = 430
    coord_y1: int = 81
    coord_x2: int = 600
    coord_y2: int = 95

    @property
    def database_url(self) -> str:
        """Формирует строку подключения к базе данных."""
        if self.db_in_pg is True:
            host = 'localhost' if self.for_local else self.db_host
            return (
                f'postgresql+asyncpg://'
                f'{self.postgres_user}:{self.postgres_password}'
                f'@{host}:{self.db_port}/{self.postgres_db}'
            )
        return 'sqlite+aiosqlite:///./fast_toir.db'

    @property
    def get_barcode_area(self) -> tuple:
        """Сообирает координаты из задания на отгрузку в кортеж."""
        return (self.coord_x1, self.coord_y1, self.coord_x2, self.coord_y2)

    model_config = SettingsConfigDict(
        env_file='infra/.env',
        env_file_encoding=ENCODING_DEFAULT,  # Явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


# Глобальная переменная settings с экземпляром класса Settings, чтобы
# его можно было импортировать в любую часть приложения, где потребуется
# доступ к настройкам:
settings: Settings = Settings()
