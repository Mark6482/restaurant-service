from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://root:root@localhost/restaurant_service"
    kafka_bootstrap_servers: str = "localhost:9092"

    class Config:
        env_file = ".env"

settings = Settings()