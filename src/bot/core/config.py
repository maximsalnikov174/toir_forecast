from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки для подключения к боту переменных окружения."""

    tg_bot_token: str = 'bot_config'

    # для чистой работы всех сервисов в контейнерах в единой сети
    backend_api_url: str = 'http://backend:8877'

    # # если бэкенд запущен в докере на локальном хосте
    # backend_api_url: str = 'http://localhost:8877'

    # # если бэкенд запущен локально
    # backend_api_url: str = 'http://localhost:8000'

    # # при локальном запуске бота для обращения к проду 131:
    # backend_api_url: str = 'http://toir.atu.mmk.ru:8877'

    model_config = SettingsConfigDict(
        env_file='infra/.env',
        env_file_encoding='utf-8',  # Явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


settings = Settings()
