import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM API (Kimi)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.kimi.com/coding/v1"
    llm_model: str = "kimi-latest"

    # Deprecated: Qwen settings (for backward compatibility)
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # Database
    database_url: str = "sqlite:///./data/scholarlens.db"

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "")) or "./data", exist_ok=True)
