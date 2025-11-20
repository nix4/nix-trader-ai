"""Telemetry and monitoring configuration using Logfire."""

import logfire
from loguru import logger
from typing import Optional


_logfire_configured = False


def configure_logfire(
    token: Optional[str] = None,
    service_name: str = "nix-trader-ai",
    service_version: str = "0.1.0",
    environment: str = "development",
    enabled: bool = True
) -> bool:
    """Configure Logfire for application monitoring.

    Args:
        token: Logfire API token
        service_name: Name of the service
        service_version: Version of the service
        environment: Environment (development, staging, production)
        enabled: Whether to enable telemetry

    Returns:
        True if configuration was successful, False otherwise
    """
    global _logfire_configured

    if _logfire_configured:
        logger.debug("Logfire already configured")
        return True

    if not enabled:
        logger.info("Telemetry disabled, skipping Logfire configuration")
        return False

    if not token:
        logger.warning("No Logfire token provided, telemetry will not be sent")
        # Still configure Logfire in console-only mode for local development
        try:
            logfire.configure(
                send_to_logfire=False,  # Don't send to cloud
                console=False  # Disable console output (we use loguru)
            )
            _logfire_configured = True
            logger.info("Logfire configured in local-only mode (no token)")
            return True
        except Exception as e:
            logger.warning(f"Failed to configure Logfire in local mode: {e}")
            return False

    try:
        # Configure Logfire with full cloud integration
        config = logfire.configure(
            token=token,
            service_name=service_name,
            service_version=service_version,
            environment=environment,
            send_to_logfire=True,
            console=False,  # We use loguru for console logging
        )

        _logfire_configured = True
        logger.info(
            f"✓ Logfire configured successfully: {service_name} v{service_version} ({environment})"
        )
        logger.info(f"  Telemetry will be sent to Logfire cloud")
        return True

    except Exception as e:
        logger.error(f"Failed to configure Logfire with token: {e}")
        # Try minimal configuration as fallback
        try:
            logfire.configure(
                send_to_logfire=False,
                console=False
            )
            _logfire_configured = True
            logger.info("Logfire configured in fallback mode (local spans only, no cloud)")
            return True
        except Exception as fallback_error:
            logger.error(f"Failed to configure Logfire even in fallback mode: {fallback_error}")
            return False


def configure_from_settings():
    """Configure Logfire using application settings.

    This should be called early in application startup.
    """
    from ..core.config import settings

    return configure_logfire(
        token=settings.logfire_token,
        service_name=settings.logfire_service_name,
        service_version=settings.logfire_service_version,
        environment=settings.logfire_environment,
        enabled=settings.enable_telemetry
    )


def is_configured() -> bool:
    """Check if Logfire has been configured.

    Returns:
        True if Logfire is configured, False otherwise
    """
    return _logfire_configured


# Auto-configure on import if settings are available
try:
    configure_from_settings()
except Exception as e:
    logger.debug(f"Auto-configuration of Logfire skipped: {e}")
