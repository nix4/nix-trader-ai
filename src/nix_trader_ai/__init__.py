"""Nix Trader AI - Multi-agent trading application framework."""

__version__ = "0.1.0"

# Configure Logfire telemetry on import
try:
    from .utils.telemetry import configure_from_settings
    configure_from_settings()
except Exception:
    # Silently continue if Logfire configuration fails
    # Logging will happen in the telemetry module
    pass