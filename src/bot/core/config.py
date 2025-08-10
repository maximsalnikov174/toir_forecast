from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки для подключения к боту переменных окружения."""

    tg_bot_token: str = 'bot_config'
    backend_api_url: str = 'http://backend:8000'  # localhost, если снаружи

    class Config:
        """Настройки конфигурации Pydantic."""

        extra = 'ignore'


settings = Settings()
