from fastapi import FastAPI, status
import uvicorn
from fastapi.responses import JSONResponse
from datetime import datetime

from src.db.session import engine, Base
from src.utils.kafka.producer import event_producer
from src.api.v1.api import api_router

app = FastAPI(title="Restaurant Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await event_producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await event_producer.stop()

# Подключаем роутеры
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    health_status = {
        "status": "healthy", 
        "service": "restaurant-service",
        "database": "connected",
        "kafka": "connected" if event_producer.is_connected() else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    status_code = status.HTTP_200_OK
    if not event_producer.is_connected():
        health_status["status"] = "degraded"
        health_status["kafka"] = "disconnected"
        status_code = status.HTTP_207_MULTI_STATUS
    
    return JSONResponse(content=health_status, status_code=status_code)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)