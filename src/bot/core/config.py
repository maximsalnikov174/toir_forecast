from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки для подключения к боту переменных окружения."""

    tg_bot_token: str = 'bot_config'
    backend_api_url: str = 'http://backend:8877'  # localhost, если снаружи

    model_config = SettingsConfigDict(
        env_file='infra/.env',
        env_file_encoding='utf-8',  # Явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


settings = Settings()
