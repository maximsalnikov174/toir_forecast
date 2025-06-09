# Здесь будет храниться код, ответственный за подключение к базе данных:

# from contextlib import asynccontextmanager

from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import (AsyncSession,
                                    AsyncEngine,
                                    async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declared_attr, declarative_base

from toir_app.constants import NEED_ECHO_SQL
from toir_app.core.config import settings


class PreBase:

    @declared_attr
    def __tablename__(cls):
        # Именем таблицы будет название модели в нижнем регистре.
        return cls.__name__.lower()

    # Во все таблицы будет добавлено поле ID.
    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=NEED_ECHO_SQL,  # Логирование SQL-запросов (для разработки)

    # Проверка соединения перед использованием
    # для автоматического восстановления соединений
    pool_pre_ping=True
)


# COMMENT: Функция async_sessionmaker() возвращает класс сессии, поэтому
# переменную, которой присвоена функция, назовите с большой буквы:
# AsyncSessionLocal; Такое имя будет указывать, что переменной присвоен класс

# Правильная асинхронная фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Рекомендуется для асинхронных сессий
    autoflush=False  # хз че такое
)


async def get_async_session():
    """Асинхроннный генератор сессий"""
    async with AsyncSessionLocal() as async_session:
        # Генератор с сессией передается в вызывающую функцию
        yield async_session
        # когда http-запрос отработает - выполнение кода вернется сюда и при
        # выходе из контекстного менеджера - сессия будет закрыта
        #
        # try:
        #     yield async_session
        # except Exception as e:
        #     print(100 * '~')
        #     print(e)


# @asynccontextmanager
# async def get_async_session():
#     """
#     Асинхроннный генератор сессий (коммитит и закрывает сессию).
#     """
#     async with AsyncSessionLocal() as async_session:
#         try:
#             yield async_session
#             await async_session.commit()  # Фиксируем изменения, если нет ошибок
#         except Exception as e:
#             await async_session.rollback()  # Откатываем при ошибке
#             raise  # Пробрасываем исключение дальше
#         finally:
#             await async_session.close()  # Явное закрытие (опционально)
