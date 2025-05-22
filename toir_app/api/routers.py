from fastapi import APIRouter

from toir_app.api.endpoints import (service_name_router,
                                    car_router)


main_router = APIRouter()


main_router.include_router(
    service_name_router,
    prefix='/service_name',
    tags=['service_name']
)
main_router.include_router(
    car_router,
    prefix='/car',
    tags=['cars']
)
