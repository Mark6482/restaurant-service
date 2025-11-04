from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    restaurant_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

class Review(ReviewBase):
    id: int
    review_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class RestaurantWithReviews(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: str
    phone: str
    email: str
    opening_hours: Optional[dict]
    is_active: bool
    average_rating: float
    review_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    reviews: list[Review] = []

    class Config:
        from_attributes = True