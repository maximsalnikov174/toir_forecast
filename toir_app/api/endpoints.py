from fastapi import APIRouter, Body


# Создаём объект роутера.
router = APIRouter()


@router.get('/all_status')
def get_all_status():
    pass
