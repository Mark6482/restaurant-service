import json
import uuid
from datetime import datetime
from aiokafka import AIOKafkaProducer
import logging

logger = logging.getLogger(__name__)

class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_dish_created(self, dish_data: dict):
        """Отправка события создания блюда"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "dish.created",
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": "restaurant-service",
            "data": dish_data
        }
        
        try:
            await self.producer.send_and_wait(
                "dish.created",
                json.dumps(event).encode('utf-8')
            )
            logger.info(f"Dish created event sent: {dish_data['dish_id']}")
        except Exception as e:
            logger.error(f"Failed to send dish created event: {e}")

    async def send_dish_updated(self, dish_data: dict):
        """Отправка события обновления блюда"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "dish.updated",
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": "restaurant-service",
            "data": dish_data
        }
        
        try:
            await self.producer.send_and_wait(
                "dish.updated",
                json.dumps(event).encode('utf-8')
            )
            logger.info(f"Dish updated event sent: {dish_data['dish_id']}")
        except Exception as e:
            logger.error(f"Failed to send dish updated event: {e}")

    async def send_dish_availability_changed(self, dish_data: dict):
        """Отправка события изменения доступности блюда"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "dish.availability_changed",
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": "restaurant-service",
            "data": dish_data
        }
        
        try:
            await self.producer.send_and_wait(
                "dish.availability_changed",
                json.dumps(event).encode('utf-8')
            )
            logger.info(f"Dish availability changed event sent: {dish_data['dish_id']}")
        except Exception as e:
            logger.error(f"Failed to send dish availability changed event: {e}")

    async def send_restaurant_created(self, restaurant_data: dict):
        """Отправка события создания ресторана"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "restaurant.created",
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": "restaurant-service",
            "data": restaurant_data
        }
        
        try:
            await self.producer.send_and_wait(
                "restaurant.created",
                json.dumps(event).encode('utf-8')
            )
            logger.info(f"Restaurant created event sent: {restaurant_data['restaurant_id']}")
        except Exception as e:
            logger.error(f"Failed to send restaurant created event: {e}")

    async def send_dish_deleted(self, dish_data: dict):
        """Отправка события удаления блюда"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "dish.deleted",
            "timestamp": datetime.utcnow().isoformat(),
            "source_service": "restaurant-service",
            "data": dish_data
        }
        
        try:
            await self.producer.send_and_wait(
                "dish.deleted",
                json.dumps(event).encode('utf-8')
            )
            logger.info(f"Dish deleted event sent: {dish_data['dish_id']}")
        except Exception as e:
            logger.error(f"Failed to send dish deleted event: {e}")

# Глобальный экземпляр продюсера
event_producer = KafkaEventProducer()