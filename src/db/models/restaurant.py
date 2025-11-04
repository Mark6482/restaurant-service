from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.session import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    opening_hours = Column(JSON)
    is_active = Column(Boolean, default=True)
    average_rating = Column(Float, default=0.0)  # Средний рейтинг
    review_count = Column(Integer, default=0)    # Количество отзывов
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    menu_categories = relationship("MenuCategory", back_populates="restaurant")
    reviews = relationship("Review", back_populates="restaurant")  # Добавляем связь с отзывами