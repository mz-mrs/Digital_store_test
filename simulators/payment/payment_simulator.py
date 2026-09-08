import logging
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from app.enums import PaymentStatus

logger = logging.getLogger(__name__)


class PaymentSimulator:
    def __init__(
        self,
        webhook_url: str,
        api_url: str
    ) -> None:
        self.webhook_url = webhook_url
        self.api_url = api_url

    async def send_webhook(
        self,
        order_id: str,
        status: PaymentStatus,
    ) -> None:

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/orders/{order_id}",
            )
            response.raise_for_status()

            order = response.json()

            amount = order["amount"]
            currency = order['currency']

            event = {
                "event_id": f"evt_{uuid4().hex}",
                "order_id": order_id,
                "status": status,
                "amount": str(amount),
                "currency": currency,
                "created_at": datetime.now(UTC).isoformat(),
            }

            logger.info(
                "PaymentSimulator: отправка webhook "
                "order_id=%s event_id=%s",
                order_id,
                event["event_id"],
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=event,
                )

                response.raise_for_status()

            logger.info(
                "PaymentSimulator: webhook отправлен "
                "order_id=%s event_id=%s status=%s",
                order_id,
                event["event_id"],
                response.status_code,
            )

