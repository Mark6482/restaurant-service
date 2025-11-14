from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.db.models.review import Review
from src.db.models.restaurant import Restaurant
import logging

logger = logging.getLogger(__name__)

async def create_review(db: AsyncSession, review_data: dict):
    """Создание отзыва из Kafka события"""
    try:
        existing_review = await db.execute(
            select(Review).filter(Review.review_id == review_data["review_id"])
        )
        if existing_review.scalar_one_or_none():
            logger.warning(f"Review with id {review_data['review_id']} already exists")
            return None

        review = Review(
            review_id=review_data["review_id"],
            restaurant_id=review_data["restaurant_id"],
            user_id=review_data["user_id"],
            rating=review_data["rating"],
            comment=review_data.get("comment"),
        )
        
        db.add(review)
        await db.commit()
        await db.refresh(review)
        
        await update_restaurant_ratings(db, review_data["restaurant_id"])
        
        logger.info(f"Review created successfully: {review_data['review_id']}")
        return review
        
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        await db.rollback()
        return None

async def update_review(db: AsyncSession, review_data: dict):
    """Обновление отзыва из Kafka события"""
    try:
        result = await db.execute(
            select(Review).filter(Review.review_id == review_data["review_id"])
        )
        review = result.scalar_one_or_none()
        
        if not review:
            logger.warning(f"Review not found: {review_data['review_id']}")
            return None

        old_rating = review.rating
        
        review.rating = review_data["new_rating"]
        review.comment = review_data.get("new_comment")
        
        await db.commit()
        await db.refresh(review)
        
        if old_rating != review_data["new_rating"]:
            await update_restaurant_ratings(db, review.restaurant_id)
        
        logger.info(f"Review updated successfully: {review_data['review_id']}")
        return review
        
    except Exception as e:
        logger.error(f"Error updating review: {e}")
        await db.rollback()
        return None

async def delete_review(db: AsyncSession, review_data: dict):
    """Удаление отзыва из Kafka события"""
    try:
        result = await db.execute(
            select(Review).filter(Review.review_id == review_data["review_id"])
        )
        review = result.scalar_one_or_none()
        
        if not review:
            logger.warning(f"Review not found: {review_data['review_id']}")
            return None

        restaurant_id = review.restaurant_id
        await db.delete(review)
        await db.commit()
        
        await update_restaurant_ratings(db, restaurant_id)
        
        logger.info(f"Review deleted successfully: {review_data['review_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting review: {e}")
        await db.rollback()
        return False

async def update_restaurant_ratings(db: AsyncSession, restaurant_id: int):
    """Обновление агрегатных данных ресторана (средний рейтинг, количество отзывов)"""
    try:
        result = await db.execute(
            select(
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.id).label('review_count')
            ).filter(
                Review.restaurant_id == restaurant_id,
                Review.is_active == True
            )
        )
        stats = result.first()
        
        result = await db.execute(
            select(Restaurant).filter(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalar_one_or_none()
        
        if restaurant and stats.avg_rating is not None:
            restaurant.average_rating = float(stats.avg_rating)
            restaurant.review_count = stats.review_count
            await db.commit()
            logger.info(f"Updated restaurant {restaurant_id} ratings: avg={stats.avg_rating}, count={stats.review_count}")
            
    except Exception as e:
        logger.error(f"Error updating restaurant ratings: {e}")
        await db.rollback()

async def get_restaurant_reviews(db: AsyncSession, restaurant_id: int, skip: int = 0, limit: int = 100):
    """Получение отзывов ресторана"""
    result = await db.execute(
        select(Review)
        .filter(Review.restaurant_id == restaurant_id, Review.is_active == True)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_restaurant_with_reviews(db: AsyncSession, restaurant_id: int):
    """Получение ресторана с отзывами"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.reviews))
        .filter(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()