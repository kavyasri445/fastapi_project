from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "FastAPI Application"
    DEBUG: bool = True

    # Secret key used for secure file download tokens
    FILE_ACCESS_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()