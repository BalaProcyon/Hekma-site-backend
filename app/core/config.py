import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hekma Backend"
    VERSION: str = "0.1.0"
    DATABASE_URL: str
    APP_ENV: str = "dev"

@lru_cache()
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev")
    env_file = f".env.{app_env}"
    if not os.path.exists(env_file):
        env_file = ".env"

    return Settings(
        _env_file=env_file, 
        _env_file_encoding="utf-8"
    )

settings = get_settings()
