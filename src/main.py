from fastapi import FastAPI
import uvicorn
import logging

from src.db.session import engine, Base
from src.utils.kafka.producer import event_producer
from src.utils.kafka.consumer import review_consumer
from src.api.v1.api import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Restaurant Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        
        await event_producer.start()
        logger.info("Kafka producer started successfully")
        
        await review_consumer.start()
        logger.info("Kafka review consumer started successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await event_producer.stop()
    await review_consumer.stop()
    logger.info("Application shutdown complete")

app.include_router(api_router)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Restaurant Service API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)