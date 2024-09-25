# app/config/settings.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_DB_URL: str = "mongodb://localhost:27017/office_management_db"  # Default connection string
    HOST: str = "127.0.0.1"  # Default host
    PORT: int = 8000  # Default port
    DEBUG: bool = True  # Enable or disable debug mode

    class Config:
        env_file = ".env"


# Create an instance of Settings
settings = Settings()
