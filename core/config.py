from functools import lru_cache
import os
from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    DATABASE_URL : str
    ALEMBIC_DB_URL : str
    SHOW_DB_LOG : bool
    ROOT_LOG_LEVEL : str
    APP_LOG_LEVEL : str
    ERROR_LOG_LEVEL : str
    OLLAMA_URL : str
    MODEL : str
    DETECTION_PROVIDER : str
    ALLOWED_IMAGE_FORMATS : str
    MAX_IMAGE_SIZE : int
    S3_REGION: str
    S3_BUCKET_NAME : str
    AWS_ACCESS_KEY : str
    AWS_SECRET_ACCESS_KEY : str
    PRESIGNED_URL_DURATION : int
    OPEN_ROUTE_SERVICE_API_KEY : str
    DEFAULT_ORS_PROFILE : str

    model_config = SettingsConfigDict(
        extra="ignore"
    )

@lru_cache
def get_settings():
    env = os.getenv("APP_ENV", "dev")
    return Settings(
        _env_file = f".env.{env}"
    )

settings = get_settings()