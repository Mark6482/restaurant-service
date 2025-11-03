from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.menu_category import MenuCategory
from src.db.models.dish import Dish
from src.schemas.menu_category import MenuCategoryCreate, MenuCategoryUpdate

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
    existing_q = await db.execute(
        select(MenuCategory).filter(
            MenuCategory.restaurant_id == restaurant_id,
            MenuCategory.name == category.name
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        return None

    existing_idx_q = await db.execute(
        select(MenuCategory).filter(
            MenuCategory.restaurant_id == restaurant_id,
            MenuCategory.order_index == category.order_index
        )
    )
    existing_idx = existing_idx_q.scalar_one_or_none()
    if existing_idx:
        return False

    db_category = MenuCategory(restaurant_id=restaurant_id, **category.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def update_menu_category(db: AsyncSession, category_id: int, category_update: MenuCategoryUpdate):
    db_category = await get_menu_category(db, category_id)
    if db_category:
        update_data = category_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
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
    from src.services.dish import delete_dish
    
    category = await get_menu_category(db, category_id)
    if not category or category.restaurant_id != restaurant_id:
        return None
    
    dishes = await get_dishes_count_by_category(db, category_id)
    
    if dishes > 0 and not force:
        raise ValueError(f"Category contains {dishes} dishes. Use force=true to delete anyway.")
    
    # Если force=True, удаляем все блюда в категории
    if force:
        dishes_to_delete = await db.execute(select(Dish).filter(Dish.category_id == category_id))
        for dish in dishes_to_delete.scalars():
            await delete_dish(db, dish.id)
    
    await db.delete(category)
    await db.commit()
    return category