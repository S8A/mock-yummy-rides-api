from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str
    WEBHOOK_URL: str
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB_NAME: str = "yummy_rides"

settings = Settings()
