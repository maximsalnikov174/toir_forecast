from pydantic import BaseModel, ConfigDict, Field

from constants import ORGANIZATION_BASE_NAME_PATTERN, SNB_PATTERN


class UnitOfBOM(BaseModel):
    """Данные о списанном материале, полученные с помощью парсинга pdf-file."""

    delivery: int = Field(..., gt=0)
    snb: str = Field(..., pattern=SNB_PATTERN)
    material_name: str
    material_count: int = Field(..., gt=0)
    from_organization: str = Field(
        ..., pattern=ORGANIZATION_BASE_NAME_PATTERN
    )


class UnitOfBOMRead(BaseModel):
    """Список используемых материалов, расширенный id юзера и карточкой sw."""
    unit_of_bom_list: list[UnitOfBOM]
    service_work_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
