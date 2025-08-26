# from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants import SNB_DESCRIPTION, SNB_LEN  # IMG_LOCATION_LEN
from core.db import Base
# from core.config import settings


class MaintenanceBillOfMaterials(Base):
    """Модель документов с перечнем используемых материалов (без материала)."""

    # location: Mapped[str] = mapped_column(
    #     String(IMG_LOCATION_LEN),
    #     nullable=False,
    # )
    delivery: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        comment='Номер доставки, оформленной в OeBS',
    )
    bar_code: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        unique=True,
        comment='Штрих-код документа',
    )

    # Связи с другими таблицами:
    from_organization: Mapped[str] = mapped_column(
        ForeignKey('organization.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Ссылка на подразделение, с которого произошло списание'
        )
    )
    service_work_id: Mapped[int] = mapped_column(
        ForeignKey('servicework.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Ссылка на карточку работы, для которой предназначены материалы'
        )
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='Пользователь, загрузивший документ',
    )

    # Обратные связи:
    service_work: Mapped['ServiceWork'] = relationship(
        'ServiceWork',
        back_populates='docs_in_service_work',
    )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='docs_by_user',
    )
    components: Mapped[list['MaintenanceComponent']] = relationship(
        'MaintenanceComponent',
        back_populates='bom',
    )

    # @property
    # def url(self) -> str:
    #     """Получить URL документа в объектном хранилище."""
    #     scheme = 'https' if settings.minio_secure else 'http'
    #     return (f'{scheme}://{settings.minio_endpoint}/'
    #             f'{settings.minio_bucket}/{self.location}')
    #     # http://minio:9000/service_work_docs/{user_id}_{service_work_id}_{random}


class MaintenanceComponent(Base):

    snb: Mapped[str] = mapped_column(
        String(SNB_LEN),
        nullable=False,
        comment='СНБ-номер материала',
    )
    material_name: Mapped[str] = mapped_column(
        String(SNB_DESCRIPTION),
        nullable=False,
        comment='Наименование материала',
    )
    material_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='Количество использованного материала',
    )

    # Связи с другими таблицами:
    maintenance_bom_id: Mapped[int] = mapped_column(
        ForeignKey(
            MaintenanceBillOfMaterials.id,
            ondelete='CASCADE',
        ),
        nullable=False,
        index=True,
        comment=(
            'Ссылка на документ, в котором указан материал'
        )
    )

    # Обратные связи:
    bom: Mapped['MaintenanceBillOfMaterials'] = relationship(
        'MaintenanceBillOfMaterials',
        back_populates='components',
    )
