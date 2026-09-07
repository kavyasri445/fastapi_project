from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "FastAPI Application"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()