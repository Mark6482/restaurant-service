from fastapi import APIRouter

from src.api.v1.endpoints import restaurants, menu_categories, dishes

api_router = APIRouter()

api_router.include_router(restaurants.router, prefix="/restaurants", tags=["restaurants"])
api_router.include_router(menu_categories.router, prefix="/restaurants/{restaurant_id}/menu/categories", tags=["menu-categories"])
api_router.include_router(dishes.router, prefix="/restaurants/{restaurant_id}/menu/dishes", tags=["dishes"])