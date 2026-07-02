import httpx

from app.core.config import settings

_TELEGRAM_BASE_URL = "https://api.telegram.org"


class TelegramNotifier:
    """Envía alertas a un chat de Telegram. Si no hay credenciales configuradas, no hace nada."""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        self._bot_token = bot_token or settings.telegram_bot_token
        self._chat_id = chat_id or settings.telegram_chat_id

    @property
    def is_configured(self) -> bool:
        return bool(self._bot_token and self._chat_id)

    async def send_message(self, text: str) -> None:
        if not self.is_configured:
            return

        url = f"{_TELEGRAM_BASE_URL}/bot{self._bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chat_id": self._chat_id, "text": text})
