from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.deps import get_db
from src.schemas.dish import Dish, DishCreate, DishUpdate, DishAvailability
from src.services.dish import (
    get_dish, get_dishes, create_dish, update_dish, 
    update_dish_availability, delete_dish
)
from src.services.menu_category import get_menu_category

router = APIRouter()

@router.get("/{dish_id}", response_model=Dish)
async def read_dish(
    restaurant_id: int, 
    dish_id: int, 
    db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return dish

@router.get("/categories/{category_id}/dishes", response_model=List[Dish])
async def read_dishes_in_category(
    restaurant_id: int, 
    category_id: int, 
    db: AsyncSession = Depends(get_db)
):
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    return await get_dishes(db, category_id)

@router.post("/categories/{category_id}/dishes", response_model=Dish, status_code=status.HTTP_201_CREATED)
async def create_dish_for_category(
    restaurant_id: int, 
    category_id: int, 
    dish: DishCreate, 
    db: AsyncSession = Depends(get_db)
):
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    return await create_dish(db, category_id, dish)

@router.put("/{dish_id}", response_model=Dish)
async def update_dish_in_menu(
    restaurant_id: int, 
    dish_id: int, 
    dish_update: DishUpdate, 
    db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return await update_dish(db, dish_id, dish_update)

@router.put("/{dish_id}/availability", response_model=Dish)
async def update_dish_availability_status(
    restaurant_id: int, 
    dish_id: int, 
    availability: DishAvailability, 
    db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return await update_dish_availability(db, dish_id, availability)

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish_from_menu(
    restaurant_id: int, 
    dish_id: int, 
    db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    await delete_dish(db, dish_id)