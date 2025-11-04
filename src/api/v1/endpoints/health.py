from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from src.utils.kafka.producer import event_producer
from src.utils.kafka.consumer import review_consumer

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        kafka_producer_status = "connected" if event_producer.is_connected() else "disconnected"
        kafka_consumer_status = "connected" if review_consumer.is_connected() else "disconnected"
        
        health_status = {
            "status": "healthy", 
            "service": "restaurant-service",
            "database": "connected",
            "kafka_producer": kafka_producer_status,
            "kafka_consumer": kafka_consumer_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code = 200
        if kafka_producer_status == "disconnected" or kafka_consumer_status == "disconnected":
            health_status["status"] = "degraded"
            status_code = 207
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        error_status = {
            "status": "error",
            "service": "restaurant-service", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=error_status, status_code=500)