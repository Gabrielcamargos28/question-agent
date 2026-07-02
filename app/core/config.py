from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Target API (Where questions will be registered)
    TARGET_API_BASE_URL: str = ""
    TARGET_API_TOKEN: str = ""

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
    COSTS_FILE: str = "logs/costs.md"

    # Pricing per 1M tokens (Approximate values for Gemini 1.5/2.0 Flash)
    # Price in USD
    MODEL_PRICING: dict = {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    }

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
