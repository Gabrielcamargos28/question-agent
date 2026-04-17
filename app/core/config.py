from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Target API (Where questions will be registered)
    TARGET_API_BASE_URL: str = "https://api.yoursystem.com"
    TARGET_API_TOKEN: str = "your_token"

    # AI Models
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Agent Settings
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    ITERATIONS_FILE: str = "logs/iteration_contexts.md"
    QUESTIONS_FILE: str = "logs/questions_log.md"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
