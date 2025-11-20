"""Slack notification service for sending alerts and reports."""

from typing import Any, Dict, Optional
import httpx
from loguru import logger


class SlackService:
    """Service for sending notifications to Slack channels."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: Optional[str] = None
    ):
        """Initialize Slack service.

        Args:
            webhook_url: Slack webhook URL for posting messages
            bot_token: Slack bot token for using API
            default_channel: Default channel to post to (when using bot token)
        """
        # Import settings here to avoid circular imports
        from ..core.config import settings

        self.webhook_url = webhook_url or settings.slack_webhook_url
        self.bot_token = bot_token or settings.slack_bot_token
        self.default_channel = default_channel or settings.slack_default_channel

        if not self.webhook_url and not self.bot_token:
            logger.warning(
                "No Slack credentials configured. Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN "
                "environment variable to enable notifications."
            )

    async def send_message(
        self,
        message: Dict[str, Any],
        channel: Optional[str] = None
    ) -> bool:
        """Send a message to Slack.

        Args:
            message: Message payload (can include blocks for rich formatting)
            channel: Channel to post to (only used with bot token)

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            if self.webhook_url:
                return await self._send_via_webhook(message)
            elif self.bot_token:
                return await self._send_via_api(message, channel or self.default_channel)
            else:
                logger.warning("No Slack configuration available, skipping notification")
                # Log the message that would have been sent
                logger.info(f"Would have sent to Slack: {message.get('text', 'No text')}")
                return False
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False

    async def _send_via_webhook(self, message: Dict[str, Any]) -> bool:
        """Send message using webhook URL.

        Args:
            message: Message payload

        Returns:
            True if successful
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.webhook_url,
                json=message
            )
            response.raise_for_status()

        logger.info("Message sent to Slack via webhook")
        return True

    async def _send_via_api(self, message: Dict[str, Any], channel: str) -> bool:
        """Send message using Slack API.

        Args:
            message: Message payload
            channel: Channel to post to

        Returns:
            True if successful
        """
        url = "https://slack.com/api/chat.postMessage"

        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": channel,
            **message
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error', 'Unknown error')}")

        logger.info(f"Message sent to Slack channel {channel} via API")
        return True

    async def send_simple_message(self, text: str, channel: Optional[str] = None) -> bool:
        """Send a simple text message to Slack.

        Args:
            text: Message text
            channel: Channel to post to (only used with bot token)

        Returns:
            True if successful
        """
        message = {"text": text}
        return await self.send_message(message, channel)

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        fields: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a formatted alert to Slack.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (info, warning, error, success)
            fields: Additional fields to include
            channel: Channel to post to

        Returns:
            True if successful
        """
        # Map severity to colors
        color_map = {
            "info": "#36a64f",      # Green
            "success": "#2eb886",   # Bright green
            "warning": "#ff9900",   # Orange
            "error": "#ff0000",     # Red
        }

        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "🚨",
        }

        color = color_map.get(severity, "#808080")
        emoji = emoji_map.get(severity, "📢")

        # Build fields section
        field_blocks = []
        if fields:
            for key, value in fields.items():
                field_blocks.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                })

        slack_message = {
            "text": f"{emoji} {title}",
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{emoji} {title}*\n{message}"
                            }
                        }
                    ]
                }
            ]
        }

        # Add fields if present
        if field_blocks:
            slack_message["attachments"][0]["blocks"].append({
                "type": "section",
                "fields": field_blocks
            })

        return await self.send_message(slack_message, channel)

    async def send_trading_alert(
        self,
        symbol: str,
        alert_type: str,
        message: str,
        price: Optional[float] = None,
        details: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a trading-specific alert.

        Args:
            symbol: Trading symbol (e.g., "XAU/USD")
            alert_type: Type of alert (e.g., "SENTIMENT_CHANGE", "PRICE_ALERT")
            message: Alert message
            price: Current price
            details: Additional details
            channel: Channel to post to

        Returns:
            True if successful
        """
        fields = {"Symbol": symbol, "Alert Type": alert_type}

        if price is not None:
            fields["Current Price"] = f"${price:,.2f}"

        if details:
            fields.update(details)

        return await self.alert(
            title=f"Trading Alert: {symbol}",
            message=message,
            severity="warning",
            fields=fields,
            channel=channel
        )


# Convenience function for quick alerts
async def send_slack_alert(text: str, channel: Optional[str] = None) -> bool:
    """Quick function to send a simple Slack alert.

    Args:
        text: Message text
        channel: Channel to post to

    Returns:
        True if successful
    """
    service = SlackService()
    return await service.send_simple_message(text, channel)
