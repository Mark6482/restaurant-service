from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models import Restaurant, MenuCategory, Dish
from app.schemas import RestaurantCreate, RestaurantUpdate, MenuCategoryCreate, MenuCategoryUpdate, DishCreate, DishUpdate, DishAvailability


from app.kafka.producer import event_producer

async def create_dish(db: AsyncSession, category_id: int, dish: DishCreate):
    db_dish = Dish(category_id=category_id, **dish.dict())
    db.add(db_dish)
    await db.commit()
    await db.refresh(db_dish)
    
    # Получаем информацию о категории для события
    from sqlalchemy.future import select
    result = await db.execute(select(MenuCategory).filter(MenuCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    # Отправляем событие создания блюда
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
        
        # Получаем информацию о категории для события
        from sqlalchemy.future import select
        result = await db.execute(
            select(MenuCategory).filter(MenuCategory.id == db_dish.category_id)
        )
        category = result.scalar_one_or_none()
        
        # Отправляем событие обновления блюда
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
        
        # Получаем информацию о категории для события
        from sqlalchemy.future import select
        result = await db.execute(
            select(MenuCategory).filter(MenuCategory.id == db_dish.category_id)
        )
        category = result.scalar_one_or_none()
        
        # Отправляем событие изменения доступности
        dish_data = {
            "dish_id": db_dish.id,
            "restaurant_id": category.restaurant_id,
            "name": db_dish.name,
            "is_available": db_dish.is_available
        }
        await event_producer.send_dish_availability_changed(dish_data)
        
    return db_dish

async def create_restaurant(db: AsyncSession, restaurant: RestaurantCreate):
    db_restaurant = Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
    
    # Отправляем событие создания ресторана
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

# Restaurant CRUD
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


async def update_menu_category(db: AsyncSession, category_id: int, category_update: MenuCategoryUpdate):
    db_category = await get_menu_category(db, category_id)
    if db_category:
        update_data = category_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        await db.commit()
        await db.refresh(db_category)
    return db_category

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

# Menu Category CRUD
async def get_menu_categories(db: AsyncSession, restaurant_id: int):
    result = await db.execute(
        select(MenuCategory)
        .filter(MenuCategory.restaurant_id == restaurant_id)
        .order_by(MenuCategory.order_index)
    )
    return result.scalars().all()

async def get_menu_category(db: AsyncSession, category_id: int):
    result = await db.execute(
        select(MenuCategory).filter(MenuCategory.id == category_id)
    )
    return result.scalar_one_or_none()

async def create_menu_category(db: AsyncSession, restaurant_id: int, category: MenuCategoryCreate):
    # Uniqueness: prevent duplicate category names per restaurant
    existing_q = await db.execute(
        select(MenuCategory).filter(
            MenuCategory.restaurant_id == restaurant_id,
            MenuCategory.name == category.name
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        return None

    # Also ensure order_index is unique within the same restaurant
    existing_idx_q = await db.execute(
        select(MenuCategory).filter(
            MenuCategory.restaurant_id == restaurant_id,
            MenuCategory.order_index == category.order_index
        )
    )
    existing_idx = existing_idx_q.scalar_one_or_none()
    if existing_idx:
        # Use a sentinel object with id None to indicate unique index violation (handled in endpoint)
        return False

    db_category = MenuCategory(restaurant_id=restaurant_id, **category.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def get_dishes_count_by_category(db: AsyncSession, category_id: int):
    result = await db.execute(
        select(Dish).filter(Dish.category_id == category_id)
    )
    dishes = result.scalars().all()
    return len(dishes)


async def delete_dish(db: AsyncSession, dish_id: int):
    """Удалить блюдо и отправить событие"""
    db_dish = await get_dish(db, dish_id)
    if not db_dish:
        return None
    
    # Получаем информацию о категории и ресторане для события
    from sqlalchemy.future import select
    result = await db.execute(
        select(MenuCategory, Restaurant)
        .join(Restaurant, MenuCategory.restaurant_id == Restaurant.id)
        .filter(MenuCategory.id == db_dish.category_id)
    )
    row = result.first()
    if row:
        category, restaurant = row
        
        # Сохраняем данные для события перед удалением
        dish_data = {
            "dish_id": db_dish.id,
            "restaurant_id": restaurant.id,
            "category_id": category.id,
            "name": db_dish.name,
            "restaurant_name": restaurant.name
        }
        
        # Удаляем блюдо
        await db.delete(db_dish)
        await db.commit()
        
        # Отправляем событие удаления блюда
        await event_producer.send_dish_deleted(dish_data)
        
        return dish_data
    
    # Если не нашли связанные данные, просто удаляем
    await db.delete(db_dish)
    await db.commit()
    return {"dish_id": dish_id}

async def delete_menu_category(db: AsyncSession, restaurant_id: int, category_id: int, force: bool = False):
    category = await get_menu_category(db, category_id)
    if not category or category.restaurant_id != restaurant_id:
        return None
    
    dishes = await get_dishes(db, category_id)
    
    if dishes and not force:
        raise ValueError(f"Category contains {len(dishes)} dishes. Use force=true to delete anyway.")
    
    for dish in dishes:
        await delete_dish(db, dish.id)
    
    await db.delete(category)
    await db.commit()
    return category

# Dish CRUD
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

# NOTE: the create_dish implementation above already emits Kafka events.
# Remove duplicate non-emitting implementation to avoid overriding the proper one.


# Composite queries
async def get_restaurant_with_menu(db: AsyncSession, restaurant_id: int):
    result = await db.execute(
        select(Restaurant)
        .options(
            selectinload(Restaurant.menu_categories)
            .selectinload(MenuCategory.dishes)
        )
        .filter(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()