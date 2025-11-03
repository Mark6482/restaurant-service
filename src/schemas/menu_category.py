from pydantic import BaseModel
from typing import Optional, List
from src.schemas.dish import Dish

class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    order_index: int = 0

class MenuCategoryCreate(MenuCategoryBase):
    pass

class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class MenuCategory(MenuCategoryBase):
    id: int
    restaurant_id: int
    is_active: bool

    class Config:
        from_attributes = True

class MenuCategoryWithDishes(MenuCategory):
    dishes: List[Dish] = []