from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    storage_path: str = Field(default="./storage", alias="STORAGE_PATH")
    file_ttl_seconds: int = Field(default=86400, alias="FILE_TTL_SECONDS")

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()