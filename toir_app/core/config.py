from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = 'Приложение ТОиР'
    database_url: str  # Обязательный параметр без значения по умолчанию

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',  # Рекомендуется явно указать кодировку
        extra='ignore'  # Игнорировать лишние переменные
    )


# Явно указал тип для переменной settings и добавил type checking коммент
settings: Settings = Settings()  # type: ignore[call-arg]

print(settings.database_url)  # Должно показать значение из .env
