from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
