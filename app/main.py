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
    """Получить список ресторанов"""
    restaurants = await get_restaurants(db, skip=skip, limit=limit)
    return restaurants

@app.post("/restaurants", response_model=Restaurant, status_code=status.HTTP_201_CREATED)
async def create_new_restaurant(restaurant: RestaurantCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый ресторан"""
    created_restaurant = await create_restaurant(db, restaurant)
    
    # Отправляем событие о создании ресторана
    restaurant_data = {
        "restaurant_id": created_restaurant.id,
        "name": created_restaurant.name,
        "description": created_restaurant.description,
        "address": created_restaurant.address,
        "phone": created_restaurant.phone,
        "email": str(created_restaurant.email),
        "opening_hours": created_restaurant.opening_hours,
        "is_active": created_restaurant.is_active
    }
    await event_producer.send_restaurant_created(restaurant_data)
    
    return created_restaurant

@app.put("/restaurants/{restaurant_id}", response_model=Restaurant)
async def update_restaurant_endpoint(
    restaurant_id: int, 
    restaurant_update: RestaurantUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Обновить информацию о ресторане"""
    db_restaurant = await update_restaurant(db, restaurant_id, restaurant_update)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@app.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant_by_id(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить ресторан"""
    db_restaurant = await delete_restaurant(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

# Menu endpoints
@app.get("/restaurants/{restaurant_id}/menu", response_model=RestaurantWithMenu)
async def read_restaurant_menu(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    """Получить полное меню ресторана с категориями и блюдами"""
    restaurant = await get_restaurant_with_menu(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@app.get("/restaurants/{restaurant_id}/menu/categories", response_model=List[MenuCategory])
async def read_menu_categories(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    """Получить категории меню ресторана"""
    categories = await get_menu_categories(db, restaurant_id)
    return categories

@app.post("/restaurants/{restaurant_id}/menu/categories", response_model=MenuCategory, status_code=status.HTTP_201_CREATED)
async def create_menu_category_for_restaurant(
    restaurant_id: int, category: MenuCategoryCreate, db: AsyncSession = Depends(get_db)
):
    """Создать категорию меню для ресторана"""
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
    """Обновить категорию меню"""
    # Проверяем, что категория принадлежит ресторану
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    updated_category = await update_menu_category(db, category_id, category_update)
    if updated_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return updated_category

@app.delete("/restaurants/{restaurant_id}/menu/categories/{category_id}", response_model=DeleteResponse)
async def delete_menu_category_endpoint(
    restaurant_id: int, 
    category_id: int, 
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Удалить категорию меню"""
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
    """Получить информацию о блюде"""
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Проверяем, что блюдо принадлежит ресторану
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
    """Получить блюда в категории"""
    # Проверяем, что категория принадлежит ресторану
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    return await get_dishes(db, category_id)

@app.post("/restaurants/{restaurant_id}/menu/categories/{category_id}/dishes", response_model=Dish, status_code=status.HTTP_201_CREATED)
async def create_dish_for_category(
    restaurant_id: int, category_id: int, dish: DishCreate, db: AsyncSession = Depends(get_db)
):
    """Создать блюдо в категории"""
    # Проверяем, что категория принадлежит ресторану
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    created_dish = await create_dish(db, category_id, dish)
    
    # Отправляем событие о создании блюда
    dish_data = {
        "dish_id": created_dish.id,
        "restaurant_id": restaurant_id,
        "category_id": category_id,
        "name": created_dish.name,
        "description": created_dish.description,
        "price": float(created_dish.price),
        "is_available": created_dish.is_available,
        "image_url": created_dish.image_url,
        "preparation_time": created_dish.preparation_time,
        "ingredients": created_dish.ingredients,
        "allergens": created_dish.allergens
    }
    await event_producer.send_dish_created(dish_data)
    
    return created_dish

@app.put("/restaurants/{restaurant_id}/menu/dishes/{dish_id}", response_model=Dish)
async def update_dish_in_menu(
    restaurant_id: int, dish_id: int, dish_update: DishUpdate, db: AsyncSession = Depends(get_db)
):
    """Обновить информацию о блюде"""
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Проверяем, что блюдо принадлежит ресторану
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    updated_dish = await update_dish(db, dish_id, dish_update)
    
    # Отправляем событие об обновлении блюда
    dish_data = {
        "dish_id": updated_dish.id,
        "restaurant_id": restaurant_id,
        "category_id": updated_dish.category_id,
        "name": updated_dish.name,
        "description": updated_dish.description,
        "price": float(updated_dish.price),
        "is_available": updated_dish.is_available,
        "image_url": updated_dish.image_url,
        "preparation_time": updated_dish.preparation_time,
        "ingredients": updated_dish.ingredients,
        "allergens": updated_dish.allergens
    }
    await event_producer.send_dish_updated(dish_data)
    
    return updated_dish

@app.put("/restaurants/{restaurant_id}/menu/dishes/{dish_id}/availability", response_model=Dish)
async def update_dish_availability_status(
    restaurant_id: int, dish_id: int, availability: DishAvailability, db: AsyncSession = Depends(get_db)
):
    """Обновить доступность блюда"""
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Проверяем, что блюдо принадлежит ресторану
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    updated_dish = await update_dish_availability(db, dish_id, availability)
    
    # Отправляем событие об изменении доступности
    dish_data = {
        "dish_id": updated_dish.id,
        "restaurant_id": restaurant_id,
        "is_available": updated_dish.is_available
    }
    await event_producer.send_dish_availability_changed(dish_data)
    
    return updated_dish

@app.delete("/restaurants/{restaurant_id}/menu/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish_from_menu(restaurant_id: int, dish_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить блюдо из меню"""
    dish = await get_dish(db, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Проверяем, что блюдо принадлежит ресторану
    category = await get_menu_category(db, dish.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Dish not found in this restaurant")
    
    await delete_dish(db, dish_id)

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "restaurant-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)