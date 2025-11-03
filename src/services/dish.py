from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.dish import Dish
from src.db.models.menu_category import MenuCategory
from src.db.models.restaurant import Restaurant
from src.schemas.dish import DishCreate, DishUpdate, DishAvailability
from src.utils.kafka.producer import event_producer

async def get_dishes(db: AsyncSession, category_id: int):
    result = await db.execute(
        select(Dish)
        .filter(Dish.category_id == category_id)
        .order_by(Dish.name)
    )
    return result.scalars().all()

async def get_dish(db: AsyncSession, dish_id: int):
    result = await db.execute(
        select(Dish).filter(Dish.id == dish_id)
    )
    return result.scalar_one_or_none()

async def create_dish(db: AsyncSession, category_id: int, dish: DishCreate):
    db_dish = Dish(category_id=category_id, **dish.dict())
    db.add(db_dish)
    await db.commit()
    await db.refresh(db_dish)
    
    result = await db.execute(select(MenuCategory).filter(MenuCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    dish_data = {
        "dish_id": db_dish.id,
        "restaurant_id": category.restaurant_id,
        "category_id": category_id,
        "name": db_dish.name,
        "description": db_dish.description,
        "price": float(db_dish.price),
        "ingredients": db_dish.ingredients or [],
        "allergens": db_dish.allergens or [],
        "preparation_time": db_dish.preparation_time,
        "is_available": db_dish.is_available,
        "image_url": db_dish.image_url
    }
    await event_producer.send_dish_created(dish_data)
    
    return db_dish

async def update_dish(db: AsyncSession, dish_id: int, dish_update: DishUpdate):
    db_dish = await get_dish(db, dish_id)
    if db_dish:
        update_data = dish_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_dish, field, value)
        await db.commit()
        await db.refresh(db_dish)
        
        result = await db.execute(
            select(MenuCategory).filter(MenuCategory.id == db_dish.category_id)
        )
        category = result.scalar_one_or_none()
        
        dish_data = {
            "dish_id": db_dish.id,
            "restaurant_id": category.restaurant_id,
            "category_id": db_dish.category_id,
            "name": db_dish.name,
            "description": db_dish.description,
            "price": float(db_dish.price),
            "ingredients": db_dish.ingredients or [],
            "allergens": db_dish.allergens or [],
            "preparation_time": db_dish.preparation_time,
            "is_available": db_dish.is_available,
            "image_url": db_dish.image_url
        }
        await event_producer.send_dish_updated(dish_data)
        
    return db_dish

async def update_dish_availability(db: AsyncSession, dish_id: int, availability: DishAvailability):
    db_dish = await get_dish(db, dish_id)
    if db_dish:
        db_dish.is_available = availability.is_available
        await db.commit()
        await db.refresh(db_dish)
        
        result = await db.execute(
            select(MenuCategory).filter(MenuCategory.id == db_dish.category_id)
        )
        category = result.scalar_one_or_none()
        
        dish_data = {
            "dish_id": db_dish.id,
            "restaurant_id": category.restaurant_id,
            "name": db_dish.name,
            "is_available": db_dish.is_available
        }
        await event_producer.send_dish_availability_changed(dish_data)
        
    return db_dish

async def delete_dish(db: AsyncSession, dish_id: int):
    db_dish = await get_dish(db, dish_id)
    if not db_dish:
        return None
    
    result = await db.execute(
        select(MenuCategory, Restaurant)
        .join(Restaurant, MenuCategory.restaurant_id == Restaurant.id)
        .filter(MenuCategory.id == db_dish.category_id)
    )
    row = result.first()
    if row:
        category, restaurant = row
        
        dish_data = {
            "dish_id": db_dish.id,
            "restaurant_id": restaurant.id,
            "category_id": category.id,
            "name": db_dish.name,
            "restaurant_name": restaurant.name
        }
        
        await db.delete(db_dish)
        await db.commit()
        
        await event_producer.send_dish_deleted(dish_data)
        
        return dish_data
    
    await db.delete(db_dish)
    await db.commit()
    return {"dish_id": dish_id}