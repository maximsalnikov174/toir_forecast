from fastapi import APIRouter

from toir_app.api.endpoints import (service_name_router,
                                    car_router,
                                    service_work_router,
                                    special_status_router)


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
main_router.include_router(
    service_work_router,
    prefix='/service_work',
    tags=['service_work']
)
main_router.include_router(
    special_status_router,
    prefix='/special_status',
    tags=['special_status']
)
