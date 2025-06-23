from pydantic import BaseModel, Field


class ServiceWorkStateBase(BaseModel):
    with_open_zvr: int = Field(..., title='С открытыми ЗВР')
    de_facto_completed: int = Field(..., title='Фактически завершены')
    without_zvr: int = Field(..., title='Пустые (без ЗВР)')

    class Config:
        from_attributes = True
