from pymongo import MongoClient
from pydantic_settings import BaseSettings


# Load database configuration directly
class Settings(BaseSettings):
    MONGO_DB_URL: str = "mongodb://localhost:27017/office_management_db"

    class Config:
        env_file = ".env"  # Keep this to read from .env if needed


# Instantiate the settings
settings = Settings()

# Initialize the MongoDB client
client = MongoClient(settings.MONGO_DB_URL)


# Define a function to connect to the database and return it
def connect_db():
    # Explicitly select the database
    db = client.get_default_database()  # This will use the database defined in the connection string

    # Optionally, list collections to confirm connection
    try:
        collections = db.list_collection_names()
        print(f"Collections in {db.name}: {collections}")
    except Exception as e:
        print(f"Error listing collections: {e}")

    return db


# Connect to the database and return the db instance
db = connect_db()
