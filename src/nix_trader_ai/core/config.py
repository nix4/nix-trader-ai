"""Application configuration."""

from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import Field
from pydantic_settings import BaseSettings
from ..models import InstrumentType


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    alpha_vantage_api_key: str = Field(alias="ALPHA_VANTAGE_API_KEY")
    newsapi_key: Optional[str] = Field(default=None, alias="NEWSAPI_KEY")

    # Interactive Brokers Configuration
    ib_host: str = Field(default="127.0.0.1", alias="IB_HOST")
    ib_port: int = Field(default=7497, alias="IB_PORT")  # 7497 for paper trading, 7496 for live
    ib_client_id: int = Field(default=1, alias="IB_CLIENT_ID")
    enable_ib: bool = Field(default=False, alias="ENABLE_IB")  # Enable IB integration

    # Trading Configuration
    min_risk_reward_ratio: Decimal = Field(default=Decimal("2.0"), alias="MIN_RISK_REWARD_RATIO")
    max_position_size_percent: Decimal = Field(default=Decimal("5.0"), alias="MAX_POSITION_SIZE_PERCENT")
    default_stop_loss_percent: Decimal = Field(default=Decimal("2.0"), alias="DEFAULT_STOP_LOSS_PERCENT")

    # Application Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # AI Model Settings
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_temperature: float = Field(default=0.3, alias="AI_TEMPERATURE")
    ai_max_tokens: Optional[int] = Field(default=None, alias="AI_MAX_TOKENS")

    # Logfire Telemetry Settings
    logfire_token: Optional[str] = Field(default=None, alias="LOGFIRE_TOKEN")
    logfire_service_name: str = Field(default="nix-trader-ai", alias="LOGFIRE_SERVICE_NAME")
    logfire_service_version: str = Field(default="0.1.0", alias="LOGFIRE_SERVICE_VERSION")
    logfire_environment: str = Field(default="development", alias="LOGFIRE_ENVIRONMENT")
    enable_telemetry: bool = Field(default=True, alias="ENABLE_TELEMETRY")

    # Slack Notification Settings
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")
    slack_bot_token: Optional[str] = Field(default=None, alias="SLACK_BOT_TOKEN")
    slack_default_channel: str = Field(default="#trading-alerts", alias="SLACK_DEFAULT_CHANNEL")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

    instruments : List[Dict[str, Any]] = [
        {
            "symbol": "XAUUSD",
            "name": "Gold vs US Dollar",
            "instrument_type": InstrumentType.COMMODITY,
            "exchange": "FX",
            "currency": "XAU",
            "sector": "Metals",
            "is_favorite": True
        },
    ]

# Global settings instance
settings = Settings()