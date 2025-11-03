from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, List
from src.schemas.menu_category import MenuCategoryWithDishes

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

class RestaurantWithMenu(Restaurant):
    menu_categories: List[MenuCategoryWithDishes] = []