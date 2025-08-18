from typing import Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class DAOBase:

    def __init__(self, model):
        self.model = model

    async def get(
            self,
            obj_id: int,
            session: AsyncSession,
    ):
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == obj_id
            )
        )
        return db_obj.scalars().first()

    async def get_multi(
            self,
            session: AsyncSession,
            sorted_param: Optional[str] = None,
    ):
        """
        Получение списка объектов с возможностью сортировки.

        ## Args:
            session: Асинхронная сессия SQLAlchemy;
            sorted_param: Поле для сортировки (опциональное).

        ## Returns:
            Список объектов модели.

        ## Raises:
            ValueError: Если указано несуществующее поле для сортировки.
        """
        try:
            stmt = select(self.model)

            if sorted_param:
                if not hasattr(self.model, sorted_param):
                    raise ValueError(
                        f'Модель {self.model.__name__} '
                        f'не имеет атрибута {sorted_param}.'
                    )
                stmt = stmt.order_by(getattr(self.model, sorted_param))

            db_objs = await session.execute(stmt)
            return db_objs.scalars().all()

        except Exception:
            return None  # FIXME должен сообщить об ошибке в запросе

    async def create(
            self,
            obj_in,
            session: AsyncSession,
    ):
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db_obj,
            obj_in,
            session: AsyncSession,
    ):
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(
            self,
            db_obj,
            session: AsyncSession,
    ):
        await session.delete(db_obj)
        await session.commit()
        return db_obj

    async def get_by_attribute(
            self,
            attr_name: str,
            attr_value: str,
            session: AsyncSession,
    ):
        attr = getattr(self.model, attr_name)
        db_obj = await session.execute(
            select(self.model).where(attr == attr_value)
        )
        return db_obj.scalars().first()
