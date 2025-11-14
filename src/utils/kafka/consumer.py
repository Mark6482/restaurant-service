import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from src.core.config import settings
from src.db.session import AsyncSessionLocal
from src.services.review import create_review, update_review, delete_review

logger = logging.getLogger(__name__)

class KafkaReviewConsumer:
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.consumer = None
        self._is_connected = False

    async def start(self):
        try:
            logger.info(f"Starting Kafka consumer with bootstrap servers: {self.bootstrap_servers}")
            self.consumer = AIOKafkaConsumer(
                "restaurant.review_created",
                "restaurant.review_updated", 
                "restaurant.review_deleted",
                bootstrap_servers=self.bootstrap_servers,
                group_id="restaurant-service-reviews-v2",
                enable_auto_commit=True,
                auto_offset_reset="earliest", 
            )
            await self.consumer.start()
            self._is_connected = True
            logger.info("Kafka consumer started successfully")
            
            asyncio.create_task(self.consume_messages())
            
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self._is_connected = False

    async def stop(self):
        if self.consumer and self._is_connected:
            try:
                await self.consumer.stop()
                self._is_connected = False
                logger.info("Kafka consumer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")

    def is_connected(self):
        return self._is_connected

    async def consume_messages(self):
        """Основной цикл обработки сообщений"""
        logger.info("Starting to consume messages from Kafka...")
        try:
            async for msg in self.consumer:
                try:
                    logger.info(f"Received message: topic={msg.topic}, partition={msg.partition}, offset={msg.offset}")
                    event_data = json.loads(msg.value.decode('utf-8'))
                    logger.info(f"Parsed event: {event_data['event_type']}")
                    await self.handle_event(msg.topic, event_data)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in consume loop: {e}")

    async def handle_event(self, topic: str, event_data: dict):
        """Обработка события в зависимости от топика"""
        logger.info(f"Handling event from topic: {topic}")
        async with AsyncSessionLocal() as db:
            try:
                if topic == "restaurant.review_created":
                    await self.handle_review_created(db, event_data)
                elif topic == "restaurant.review_updated":
                    await self.handle_review_updated(db, event_data)
                elif topic == "restaurant.review_deleted":
                    await self.handle_review_deleted(db, event_data)
                    
            except Exception as e:
                logger.error(f"Error handling event from topic {topic}: {e}")
                await db.rollback()

    async def handle_review_created(self, db, event_data: dict):
        """Обработка создания отзыва"""
        logger.info(f"Creating review: {event_data['data']['review_id']}")
        review_data = {
            "review_id": event_data["data"]["review_id"],
            "restaurant_id": event_data["data"]["restaurant_id"],
            "user_id": event_data["data"]["user_id"],
            "rating": event_data["data"]["rating"],
            "comment": event_data["data"].get("comment"),
        }
        result = await create_review(db, review_data)
        if result:
            logger.info(f"Successfully created review: {event_data['data']['review_id']}")
        else:
            logger.error(f"Failed to create review: {event_data['data']['review_id']}")

    async def handle_review_updated(self, db, event_data: dict):
        """Обработка обновления отзыва"""
        logger.info(f"Updating review: {event_data['data']['review_id']}")
        review_data = {
            "review_id": event_data["data"]["review_id"],
            "new_rating": event_data["data"]["new_rating"],
            "new_comment": event_data["data"].get("new_comment"),
        }
        result = await update_review(db, review_data)
        if result:
            logger.info(f"Successfully updated review: {event_data['data']['review_id']}")
        else:
            logger.error(f"Failed to update review: {event_data['data']['review_id']}")

    async def handle_review_deleted(self, db, event_data: dict):
        """Обработка удаления отзыва"""
        logger.info(f"Deleting review: {event_data['data']['review_id']}")
        review_data = {
            "review_id": event_data["data"]["review_id"],
        }
        result = await delete_review(db, review_data)
        if result:
            logger.info(f"Successfully deleted review: {event_data['data']['review_id']}")
        else:
            logger.error(f"Failed to delete review: {event_data['data']['review_id']}")

review_consumer = KafkaReviewConsumer()