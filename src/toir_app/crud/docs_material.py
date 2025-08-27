# import uuid
# from io import BytesIO

# from fastapi import UploadFile
# from minio import Minio
# from sqlalchemy.ext.asyncio import AsyncSession
# from starlette.concurrency import run_in_threadpool

# from core.config import settings

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import DAOBase
from models import MaintenanceBillOfMaterials, MaintenanceComponent  # User


class DocBOMDAO(DAOBase[MaintenanceBillOfMaterials]):
    """DAO для работы с моделью документа с материалами."""

    model = MaintenanceBillOfMaterials

    async def get_full(self, obj_id, session):
        stmt = (
            select(self.model)
            .where(self.model.id == obj_id)
            .options(selectinload(self.model.components))
            .limit(1)
        )
        result = await session.scalar(stmt)
        return result

    async def get_multi_by_attribute(
            self,
            attr_name: str,
            attr_value: str,
            session: AsyncSession,
    ):
        """Получение списка объектов по параметру.

        ## Args:
            attr_name: Поле модели;
            attr_value: Искомое значение;
            session: Асинхронная сессия SQLAlchemy.

        ## Returns:
            список объектов модели.
        """
        # Проверяем искомый параметр модели:
        if not hasattr(self.model, attr_name):
            raise AttributeError(
                f'У {self.model.__name__} нет атрибута {attr_name}'
            )
        attr = getattr(self.model, attr_name)

        stmt = (
            select(self.model)
            .where(attr == attr_value)
            .options(selectinload(self.model.components))
        )
        result = await session.scalars(stmt)
        return result.all()

    # async def create_with_file(
    #         self,
    #         service_work_id: int,
    #         file: UploadFile,
    #         client: Minio,
    #         user: User,
    # ) -> MaintenanceBillOfMaterials:
    #     """Создает документ (файл) в MinIO и сохраняет в БД."""
    #     object_name = f'{user.id}_{service_work_id}_{uuid.uuid4()}'
    #     # FIXME Как избежать задваивания вложенных документов?

    #     data = await file.read()

    #     if not await run_in_threadpool(
    #         client.bucket_exists,
    #         settings.minio_bucket
    #     ):
    #         await run_in_threadpool(client.make_bucket, settings.minio_bucket)

    #     await run_in_threadpool(
    #         client.put_object,
    #         settings.minio_bucket,
    #         object_name,
    #         BytesIO(data),
    #         len(data),
    #         content_type=file.content_type,
    #     )

    #     docs_material = MaintenanceBillOfMaterials(
    #         location=object_name,
    #         service_work_id=service_work_id,
    #         user=user.id
    #     )
    #     self.session.add(docs_material)
    #     await self.session.flush()
    #     return docs_material

    # async def delete_with_file(
    #         self,
    #         docs_material_id: int,
    #         client: Minio
    # ) -> bool:
    #     """Удаляет изображение и файл в MinIO."""
    #     docs_material = await self.get(docs_material_id)

    #     if docs_material is None:
    #         return False

    #     if await run_in_threadpool(
    #         client.bucket_exists,
    #         settings.minio_bucket
    #     ):
    #         await run_in_threadpool(
    #             client.remove_object,
    #             settings.minio_bucket,
    #             docs_material.location,
    #         )

    #     await self.delete(docs_material)
    #     return True


class UnitOfBOMDAO(DAOBase[MaintenanceComponent]):
    """DAO для работы с моделью используемого при сервисе материала."""

    model = MaintenanceComponent


dao_doc_bom = DocBOMDAO(MaintenanceBillOfMaterials)
dao_unit_of_bom = UnitOfBOMDAO(MaintenanceComponent)
