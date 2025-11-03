from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.restaurant import Restaurant
from src.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from src.utils.kafka.producer import event_producer

async def get_restaurants(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Restaurant)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_restaurant(db: AsyncSession, restaurant_id: int):
    result = await db.execute(
        select(Restaurant).filter(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()

async def create_restaurant(db: AsyncSession, restaurant: RestaurantCreate):
    db_restaurant = Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
    
    restaurant_data = {
        "restaurant_id": db_restaurant.id,
        "name": db_restaurant.name,
        "description": db_restaurant.description,
        "address": db_restaurant.address,
        "phone": db_restaurant.phone,
        "email": db_restaurant.email,
        "opening_hours": db_restaurant.opening_hours,
        "is_active": db_restaurant.is_active
    }
    await event_producer.send_restaurant_created(restaurant_data)
    
    return db_restaurant

async def update_restaurant(db: AsyncSession, restaurant_id: int, restaurant_update: RestaurantUpdate):
    db_restaurant = await get_restaurant(db, restaurant_id)
    if db_restaurant:
        update_data = restaurant_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_restaurant, field, value)
        await db.commit()
        await db.refresh(db_restaurant)
    return db_restaurant

async def delete_restaurant(db: AsyncSession, restaurant_id: int):
    db_restaurant = await get_restaurant(db, restaurant_id)
    if db_restaurant:
        await db.delete(db_restaurant)
        await db.commit()
    return db_restaurant

async def get_restaurant_with_menu(db: AsyncSession, restaurant_id: int):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Restaurant)
        .options(
            selectinload(Restaurant.menu_categories)
            .selectinload(Restaurant.menu_categories.property.entity.class_.dishes)
        )
        .filter(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()