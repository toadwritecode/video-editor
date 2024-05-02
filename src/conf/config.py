import os
# from pathlib import Path

from pydantic_settings import BaseSettings

# BASE_DIR = Path(__file__).resolve().parent.parent

BASE_DIR = os.getcwd()


class Settings(BaseSettings):
    AUTH_API_LOGIN: str = ''
    AUTH_API_PASSWORD: str = ''
    SECURITY_ENABLED: bool = False
    STORAGE_NAME: str = "storage"

    class Config:
        case_sensitive = True
        env_file = BASE_DIR + "/.env"


settings = Settings()