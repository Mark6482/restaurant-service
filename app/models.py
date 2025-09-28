from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    opening_hours = Column(JSON)  # {"monday": "09:00-22:00", ...}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    menu_categories = relationship("MenuCategory", back_populates="restaurant")

class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    name = Column(String)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    restaurant = relationship("Restaurant", back_populates="menu_categories")
    dishes = relationship("Dish", back_populates="category")

class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))
    name = Column(String)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    ingredients = Column(ARRAY(String))  # Список ингредиентов
    allergens = Column(ARRAY(String))    # Аллергены
    preparation_time = Column(Integer)   # Время приготовления в минутах
    is_available = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("MenuCategory", back_populates="dishes")