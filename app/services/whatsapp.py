import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.base_url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, message: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message, "preview_url": False},
        }
        return await self._post(payload)

    async def send_image(self, to: str, image_url: str, caption: str = "") -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }
        return await self._post(payload)

    async def send_document(self, to: str, document_url: str, filename: str, caption: str = "") -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
                "caption": caption,
            },
        }
        return await self._post(payload)

    async def send_motivation(self, to: str, image_url: str, quote: str, name: str, streak: int) -> None:
        """Send morning motivation: image first, then personalised quote."""
        streak_text = f"\n\n🔥 Day {streak} streak — keep going." if streak > 1 else ""
        caption = f'"{quote}"{streak_text}'
        await self.send_image(to, image_url, caption)

        follow_up = f"Morning {name} 👊 Make today count."
        await self.send_text(to, follow_up)

    async def _post(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.base_url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {response.status_code} {response.text}")
            response.raise_for_status()
            return response.json()


whatsapp_service = WhatsAppService()
