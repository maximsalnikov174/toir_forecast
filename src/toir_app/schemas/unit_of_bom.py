from pydantic import BaseModel, ConfigDict, Field

from constants import (
    BAR_CODE_PATTERN,
    ORGANIZATION_BASE_NAME_PATTERN,
    SNB_DESCRIPTION,
    SNB_PATTERN,
)

# Для справки: BOM (Bill of material) - спецификация материала


class BOMDocsDelivery(BaseModel):
    """Схема документа (метакласс)."""

    delivery: int = Field(..., gt=0)

    model_config = ConfigDict(validate_assignment=True)


class BOMDocs(BOMDocsDelivery):
    """Схема документа (расширенная подразделением)."""

    from_organization: str = (
        Field(..., pattern=ORGANIZATION_BASE_NAME_PATTERN)
    )


class UnitOfBOM(BaseModel):
    """Данные о списанном материале, полученные с помощью парсинга pdf-file."""

    snb: str = Field(..., pattern=SNB_PATTERN)
    material_name: str = Field(..., max_length=SNB_DESCRIPTION)
    material_count: int = Field(..., gt=0)


class UnitOfBOMWithDocsCreate(UnitOfBOM):
    """Схема для валидации данных при создании модели UOB."""

    maintenance_bom_id: int  # id документа.


class BOMDocsCreate(BOMDocsDelivery):
    """Схема для валидации данных при создании модели документа UOB."""

    from_organization: int
    service_work_id: int
    user_id: int
    bar_code: str = Field(..., pattern=BAR_CODE_PATTERN)
    to_insert: bool = False


class RawUnitOfBOM(BaseModel):
    """Чистая карточка с отгрузкой используемых материалов."""

    unit_of_bom_list: list[UnitOfBOM]
    unit_of_bom_doc: BOMDocs


class RawUnitOfBOMWithBarcode(RawUnitOfBOM):
    """Чистая карточка с отгрузкой используемых материалов."""

    bar_code: str = Field(..., pattern=BAR_CODE_PATTERN)


class UnitOfBOMRead(BOMDocsCreate):
    """Список используемых материалов, расширенный id юзера и карточкой sw."""

    id: int
    components: list[UnitOfBOM]

    model_config = ConfigDict(from_attributes=True)
