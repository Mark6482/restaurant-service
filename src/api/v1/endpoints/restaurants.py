from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.deps import get_db
from src.schemas.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate
from src.services.restaurant import (
    get_restaurants, create_restaurant, get_restaurant, 
    update_restaurant, delete_restaurant
)

router = APIRouter()

@router.get("/", response_model=List[Restaurant])
async def read_restaurants(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    restaurants = await get_restaurants(db, skip=skip, limit=limit)
    return restaurants

@router.post("/", response_model=Restaurant, status_code=status.HTTP_201_CREATED)
async def create_new_restaurant(
    restaurant: RestaurantCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await create_restaurant(db, restaurant)

@router.put("/{restaurant_id}", response_model=Restaurant)
async def update_restaurant_endpoint(
    restaurant_id: int, 
    restaurant_update: RestaurantUpdate, 
    db: AsyncSession = Depends(get_db)
):
    db_restaurant = await update_restaurant(db, restaurant_id, restaurant_update)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant_by_id(
    restaurant_id: int, 
    db: AsyncSession = Depends(get_db)
):
    db_restaurant = await delete_restaurant(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")