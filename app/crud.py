from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models import Restaurant, MenuCategory, Dish
from app.schemas import RestaurantCreate, RestaurantUpdate, MenuCategoryCreate, MenuCategoryUpdate, DishCreate, DishUpdate, DishAvailability

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

async def create_restaurant(db: AsyncSession, restaurant: RestaurantCreate):
    db_restaurant = Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
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

async def create_dish(db: AsyncSession, category_id: int, dish: DishCreate):
    db_dish = Dish(category_id=category_id, **dish.dict())
    db.add(db_dish)
    await db.commit()
    await db.refresh(db_dish)
    return db_dish

async def update_dish(db: AsyncSession, dish_id: int, dish_update: DishUpdate):
    db_dish = await get_dish(db, dish_id)
    if db_dish:
        update_data = dish_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_dish, field, value)
        await db.commit()
        await db.refresh(db_dish)
    return db_dish

async def update_dish_availability(db: AsyncSession, dish_id: int, availability: DishAvailability):
    db_dish = await get_dish(db, dish_id)
    if db_dish:
        db_dish.is_available = availability.is_available
        await db.commit()
        await db.refresh(db_dish)
    return db_dish

async def delete_dish(db: AsyncSession, dish_id: int):
    db_dish = await get_dish(db, dish_id)
    if db_dish:
        await db.delete(db_dish)
        await db.commit()
    return db_dish

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