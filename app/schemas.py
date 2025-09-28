from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

# Restaurant Schemas
class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    phone: str
    email: EmailStr
    opening_hours: Optional[Dict] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    opening_hours: Optional[Dict] = None
    is_active: Optional[bool] = None

class Restaurant(RestaurantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Menu Category Schemas
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

# Dish Schemas
class DishBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    ingredients: List[str] = []
    allergens: List[str] = []
    preparation_time: int
    image_url: Optional[str] = None

class DishCreate(DishBase):
    pass

class DishUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    ingredients: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    preparation_time: Optional[int] = None
    image_url: Optional[str] = None

class DishAvailability(BaseModel):
    is_available: bool

class Dish(DishBase):
    id: int
    category_id: int
    is_available: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Composite Schemas
class MenuCategoryWithDishes(MenuCategory):
    dishes: List[Dish] = []

class RestaurantWithMenu(Restaurant):
    menu_categories: List[MenuCategoryWithDishes] = []


class DeleteResponse(BaseModel):
    message: str
    deleted_id: int