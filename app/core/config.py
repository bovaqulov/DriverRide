# application/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variables"""

    # App settings
    DEBUG: bool = True

    # Bot tokens
    BOT_TOKEN: str = ""

    # Product url
    HOST: str = ""
    PORT: int

    # Payment
    BOT_PAYMENT_TOKEN: str = ""

    # Frontend url
    FRONTEND_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"
    REDIS_MAX_CONNECTIONS: int = 10

    # Localization
    LOCALES_PATH: str = "./locales"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: str = "en,uz,ru"
    API_VERSION: str = "api/v1"
    AUTH_TOKEN: str
    API_HOST: str

    # Admin
    ADMIN_IDS: str = ""

    # webhook
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = ""

    @property
    def SUPPORTED_LANGS(self) -> List[str]:
        """Get list of supported languages"""
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(',')]

    @property
    def ADMINS(self) -> List[int]:
        """Get list of admin user IDs"""
        if not self.ADMIN_IDS:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_IDS.split(',') if uid.strip()]

    @property
    def MAIN_URL(self):
        """Get main url based on DEBUG mode"""
        if self.DEBUG:
            url = f"http://{self.API_HOST}:{self.API_PORT}"
        else:
            url = f"https://{self.API_HOST}"
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()