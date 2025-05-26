toir_atu_fastapi

### Автоматическое создание файла миграций:
`alembic revision --autogenerate -m "First migration"`

### Применение миграций:
`alembic upgrade head`

### Запуск приложения через терминал:
<!-- `uvicorn toir_app.main:toir_app --host 0.0.0.0 --port 8000 --reload` -->
`uvicorn toir_app.main:toir_app --reload`