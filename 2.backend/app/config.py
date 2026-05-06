from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/capstone_db"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_supersecretkey123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    NEWS_API_KEY: str = "d7qutrpr01qtpsm0g9lgd7qutrpr01qtpsm0g9m0"

    class Config:
        env_file = ".env"

settings = Settings()
