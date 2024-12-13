from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEBHOOK_URL: str


settings = Settings()
