from typing import Optional

from minio import Minio

from core.config import settings


def get_minio_client(endpoint: Optional[str] = None) -> Minio:
    """Создает и возвращает клиент MinIO.

    Parameters
    ----------
    endpoint: str | None
        адрес MinIO, который необходимо использовать. Если не указан -
        используется `settings.minio_endpoint`.
    """
    endpoint = endpoint or settings.minio_endpoint

    return Minio(
        endpoint=endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
