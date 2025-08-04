from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    REDDIT_SCREENSHOTS_DIR: str = "img"
    DEBUG: bool = False  # ✅ Agrega esta línea si no está


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

