import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram Bot API (Direct, zero-cost, instant setup)
    TELEGRAM_BOT_TOKEN: str = ""

    # WhatsApp Meta Cloud API (Retained for future deployment)
    WHATSAPP_VERIFY_TOKEN: str = "default_verify_token"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    PHONE_NUMBER_ID: str = ""

    # WhatsApp via Evolution API (self-hosted, e.g. Docker on localhost:8080). When URL and instance are set,
    # WhatsApp messages are sent through Evolution instead of the Meta Cloud API.
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = ""

    # Google Gemini (Free Tier LLM & Multimodal Audio STT)
    GEMINI_API_KEY: str = ""
    # Cheapest models that work for new API keys: flash-lite for text, 3.5 flash-lite for audio input
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_AUDIO_MODEL: str = "gemini-3.5-flash-lite"

    # Database
    DATABASE_URL: Optional[str] = None

    # Vector Retrieval (Local Qdrant + FastEmbed)
    QDRANT_URL: Optional[str] = None  # None uses local on-disk embedded Qdrant; "http://localhost:6333" uses Docker
    QDRANT_COLLECTION: str = "authoritative_knowledge"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    # Build the collection at startup when it is missing or empty (fresh clones / ephemeral deploys)
    QDRANT_AUTO_INGEST: bool = True

    # General
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_INTERNAL_URL: str = "http://localhost:8000"
    AUTH_SECRET_KEY: str = "sca_rural_enterprise_advisor_secret_key_2026_secure"
    # Officer self-registration; switched off on the public deployment (accounts are created by an admin)
    ALLOW_PUBLIC_SIGNUP: bool = True
    # True: never fall back to synthetic benchmarks; unsupported trades return DATA_NOT_AVAILABLE.
    REAL_DATA_ONLY: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """Returns configured database URL or falls back to local SQLite."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./rural_advisor.db"

settings = Settings()
