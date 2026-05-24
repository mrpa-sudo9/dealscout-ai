
from telegram import Bot

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class TelegramPublisher(BasePublisher):
    name = "telegram"

    async def publish(self, content: Content) -> str | None:
        if not settings.telegram_bot_token or not settings.telegram_channel_id:
            self.log.warning("Telegram credentials not configured")
            return None

        bot = Bot(token=settings.telegram_bot_token)
        msg = await bot.send_message(chat_id=settings.telegram_channel_id, text=content.body[:4096])
        return str(msg.message_id)
