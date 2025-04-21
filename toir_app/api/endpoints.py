from fastapi import APIRouter, Body

from toir_app.schemas.schemas import (Status,
                                      SpecialStatusForCar,
                                      UserRole,
                                      UsersServiceName,
                                      BaseCarData,
                                      CarDataPoint,
                                      OrganizationBase,
                                      OrganizationResponse,
                                      UserBase,
                                      SpecialStatusWithTimestamp,
                                      CarModelBase,
                                      ServiceNameBase,
                                      CarBase)


# Создаём объект роутера.
router = APIRouter()


@router.get('/all_status')
def get_all_status():
    pass
