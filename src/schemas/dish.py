from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

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

class DeleteResponse(BaseModel):
    message: str
    deleted_id: int