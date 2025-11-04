from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.deps import get_db
from src.schemas.review import Review, RestaurantWithReviews
from src.services.review import get_restaurant_reviews, get_restaurant_with_reviews

router = APIRouter()

@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[Review])
async def read_restaurant_reviews(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить отзывы ресторана"""
    reviews = await get_restaurant_reviews(db, restaurant_id, skip=skip, limit=limit)
    return reviews

@router.get("/restaurants/{restaurant_id}/with-reviews", response_model=RestaurantWithReviews)
async def read_restaurant_with_reviews(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить ресторан с отзывами"""
    restaurant = await get_restaurant_with_reviews(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant