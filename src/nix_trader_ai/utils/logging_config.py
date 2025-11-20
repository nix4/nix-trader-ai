"""Logging configuration for the application."""

import sys
from pathlib import Path
from typing import Optional

import logfire
from loguru import logger

from ..core.config import settings


def setup_logging():
    """Configure application logging."""
    # Initialize Logfire if enabled and token is provided
    if settings.enable_telemetry and settings.logfire_token:
        try:
            logfire.configure(
                token=settings.logfire_token,
                service_name=settings.logfire_service_name,
                service_version=settings.logfire_service_version,
                environment=settings.logfire_environment,
            )

            # Add common instrumentation
            logfire.instrument_httpx()
            logfire.instrument_asyncio()
            logfire.instrument_pydantic()

            logger.info("Logfire telemetry initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Logfire: {e}")
    elif settings.enable_telemetry:
        logger.info("Telemetry enabled but no Logfire token provided - using local logging only")
    else:
        logger.info("Telemetry disabled")

    # Remove default handler
    logger.remove()

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Console logging with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File logging for all messages
    logger.add(
        log_dir / "nix_trader_ai.log",
        rotation="100 MB",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=True,
    )

    # Separate error log
    logger.add(
        log_dir / "errors.log",
        rotation="50 MB",
        retention="90 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=True,
    )

    # Agent-specific logging
    logger.add(
        log_dir / "agents.log",
        rotation="50 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[agent]}: {message}",
        filter=lambda record: "agent" in record["extra"],
    )

    # Service-specific logging
    logger.add(
        log_dir / "services.log",
        rotation="50 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[service]}: {message}",
        filter=lambda record: "service" in record["extra"],
    )

    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Environment: {settings.environment}")


def get_logger(component: str):
    """Get a logger for a specific component."""
    return logger.bind(component=component)