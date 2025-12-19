from pydantic import BaseModel


class ActiveServiceWorksSchema(BaseModel):
    """Список активных для ТС сервисных работ, получаемых с бэкенда."""

    id: int
    station_id: int
    zvr_number: str
    service_name: str
    car_grz: str

    @property
    def present_in_keyboard(self) -> str:
        """Объеденяет вид работ и номер ЗВР в единую строчку для клавиатуры."""
        return f'{self.service_name} | {self.zvr_number}'
