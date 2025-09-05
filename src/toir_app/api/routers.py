from fastapi import APIRouter

from api.endpoints import (
    service_name_router,
    car_router,
    service_work_router,
    special_status_router,
    station_router,
    stats_router,
    organization_router,
    role_router,
    service_status_router,
    user_router,
)

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
main_router.include_router(
    organization_router,
    prefix='/organization',
    tags=['organization']
)
main_router.include_router(
    service_status_router,
    prefix='/service_status',
    tags=['service_status', 'service_work']
)
main_router.include_router(user_router)
main_router.include_router(
    stats_router,
    prefix='/stats',
    tags=['stats']
)
main_router.include_router(
    station_router,
    prefix='/station',
    tags=['station']
)
main_router.include_router(
    role_router,
    prefix='/role',
    tags=['role']
)
