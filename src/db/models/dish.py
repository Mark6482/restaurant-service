from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from src.db.session import Base

class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))
    name = Column(String)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    ingredients = Column(ARRAY(String))
    allergens = Column(ARRAY(String))
    preparation_time = Column(Integer)
    is_available = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("MenuCategory", back_populates="dishes")