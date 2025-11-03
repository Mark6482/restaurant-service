from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.deps import get_db
from src.schemas.menu_category import MenuCategory, MenuCategoryCreate, MenuCategoryUpdate
from src.schemas.dish import DeleteResponse
from src.services.menu_category import (
    get_menu_categories, create_menu_category, get_menu_category, 
    update_menu_category, delete_menu_category, get_dishes_count_by_category
)
from src.services.restaurant import get_restaurant

router = APIRouter()

@router.get("/", response_model=List[MenuCategory])
async def read_menu_categories(
    restaurant_id: int, 
    db: AsyncSession = Depends(get_db)
):
    categories = await get_menu_categories(db, restaurant_id)
    return categories

@router.post("/", response_model=MenuCategory, status_code=status.HTTP_201_CREATED)
async def create_menu_category_for_restaurant(
    restaurant_id: int, 
    category: MenuCategoryCreate, 
    db: AsyncSession = Depends(get_db)
):
    restaurant = await get_restaurant(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    created = await create_menu_category(db, restaurant_id, category)
    if created is None:
        raise HTTPException(status_code=400, detail="Category with this name already exists for this restaurant")
    if created is False:
        raise HTTPException(status_code=400, detail="Category with this order_index already exists for this restaurant")
    return created

@router.put("/{category_id}", response_model=MenuCategory)
async def update_menu_category_endpoint(
    restaurant_id: int,
    category_id: int,
    category_update: MenuCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    category = await get_menu_category(db, category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=404, detail="Category not found in this restaurant")
    
    updated_category = await update_menu_category(db, category_id, category_update)
    return updated_category

@router.delete("/{category_id}", response_model=DeleteResponse)
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
        dishes_count = await get_dishes_count_by_category(db, category_id)
        raise HTTPException(
            status_code=400, 
            detail={
                "message": str(e),
                "dishes_count": dishes_count,
                "suggestion": "Set force=true to delete category with all dishes"
            }
        )