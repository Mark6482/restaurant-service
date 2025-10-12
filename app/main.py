from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio
import uvicorn

from app.database import get_db, engine, Base
from app.schemas import (
    Restaurant, RestaurantCreate, RestaurantUpdate,
    MenuCategory, MenuCategoryCreate, MenuCategoryUpdate,
    Dish, DishCreate, DishUpdate, DishAvailability, 
    RestaurantWithMenu, DeleteResponse
)
from app.crud import (
    get_restaurants, create_restaurant, get_restaurant, update_restaurant, delete_restaurant,
    get_menu_categories, create_menu_category, get_menu_category, update_menu_category, delete_menu_category,
    get_dishes, get_dish, create_dish, update_dish, update_dish_availability, delete_dish,
    get_restaurant_with_menu, get_dishes_count_by_category
)
from app.kafka.producer import event_producer

app = FastAPI(title="Restaurant Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await event_producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await event_producer.stop()

# Restaurant endpoints
@app.get("/restaurants", response_model=List[Restaurant])
async def read_restaurants(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    restaurants = await get_restaurants(db, skip=skip, limit=limit)
    return restaurants

@app.post("/restaurants", response_model=Restaurant, status_code=status.HTTP_201_CREATED)
async def create_new_restaurant(restaurant: RestaurantCreate, db: AsyncSession = Depends(get_db)):
    return await create_restaurant(db, restaurant)

@app.put("/restaurants/{restaurant_id}", response_model=Restaurant)
async def update_restaurant_endpoint(
    restaurant_id: int, 
    restaurant_update: RestaurantUpdate, 
    db: AsyncSession = Depends(get_db)
):
    db_restaurant = await update_restaurant(db, restaurant_id, restaurant_update)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@app.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant_by_id(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    db_restaurant = await delete_restaurant(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

# Menu endpoints
@app.get("/restaurants/{restaurant_id}/menu", response_model=RestaurantWithMenu)
async def read_restaurant_menu(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    restaurant = await get_restaurant_with_menu(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@app.get("/restaurants/{restaurant_id}/menu/categories", response_model=List[MenuCategory])
async def read_menu_categories(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    categories = await get_menu_categories(db, restaurant_id)
    return categories

@app.post("/restaurants/{restaurant_id}/menu/categories", response_model=MenuCategory, status_code=status.HTTP_201_CREATED)
async def create_menu_category_for_restaurant(
    restaurant_id: int, category: MenuCategoryCreate, db: AsyncSession = Depends(get_db)
):
    restaurant = await get_restaurant(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return await create_menu_category(db, restaurant_id, category)

@app.put("/restaurants/{restaurant_id}/menu/categories/{category_id}", response_model=MenuCategory)
async def update_menu_category_endpoint(
    restaurant_id: int,
    category_id: int,
    category_update: MenuCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, что категория принадлежит ресторану
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    # В реальной реализации добавим функцию update_menu_category в CRUD
    # Пока используем существующую логику
    return category

@app.delete("/restaurants/{restaurant_id}/menu/categories/{category_id}", response_model=DeleteResponse)
async def delete_menu_category_endpoint(
    restaurant_id: int, 
    category_id: int, 
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        deleted_category = await delete_menu_category(db, restaurant_id, category_id, force)
        if deleted_category:
            return DeleteResponse(
                message="Category deleted successfully" + (" (with all dishes)" if force else ""),
                deleted_id=category_id
            )
        else:
            raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    except ValueError as e:
        # Получаем количество блюд для информативного сообщения
        dishes_count = await get_dishes_count_by_category(db, category_id)
        raise HTTPException(
            status_code=400, 
            detail={
                "message": str(e),
                "dishes_count": dishes_count,
                "suggestion": "Set force=true to delete category with all dishes"
            }
        )

# Dish endpoints
@app.get("/restaurants/{restaurant_id}/menu/dishes/{dish_id}", response_model=Dish)
async def read_dish(restaurant_id: int, dish_id: int, db: AsyncSession = Depends(get_db)):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Verify dish belongs to restaurant
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return dish

@app.get("/restaurants/{restaurant_id}/menu/categories/{category_id}/dishes", response_model=List[Dish])
async def read_dishes_in_category(
    restaurant_id: int, 
    category_id: int, 
    db: AsyncSession = Depends(get_db)
):
    # Verify category belongs to restaurant
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    return await get_dishes(db, category_id)

@app.post("/restaurants/{restaurant_id}/menu/categories/{category_id}/dishes", response_model=Dish, status_code=status.HTTP_201_CREATED)
async def create_dish_for_category(
    restaurant_id: int, category_id: int, dish: DishCreate, db: AsyncSession = Depends(get_db)
):
    # Verify category belongs to restaurant
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    return await create_dish(db, category_id, dish)

@app.put("/restaurants/{restaurant_id}/menu/dishes/{dish_id}", response_model=Dish)
async def update_dish_in_menu(
    restaurant_id: int, dish_id: int, dish_update: DishUpdate, db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Verify dish belongs to restaurant
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return await update_dish(db, dish_id, dish_update)

@app.put("/restaurants/{restaurant_id}/menu/dishes/{dish_id}/availability", response_model=Dish)
async def update_dish_availability_status(
    restaurant_id: int, dish_id: int, availability: DishAvailability, db: AsyncSession = Depends(get_db)
):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Verify dish belongs to restaurant
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    return await update_dish_availability(db, dish_id, availability)

@app.delete("/restaurants/{restaurant_id}/menu/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish_from_menu(restaurant_id: int, dish_id: int, db: AsyncSession = Depends(get_db)):
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Verify dish belongs to restaurant
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    await delete_dish(db, dish_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)