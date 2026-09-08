import json
from uuid import UUID

import aio_pika


QUEUE_NAME = "delivery.issue"


class DeliveryPublisher:
    def __init__(
        self,
        connection: aio_pika.abc.AbstractRobustConnection,
    ) -> None:
        self.connection = connection
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def start(self) -> None:
        self.channel = await self.connection.channel()

        await self.channel.declare_queue(
            QUEUE_NAME,
            durable=True,
        )

    async def publish(self, delivery_id: UUID) -> None:
        if self.channel is None:
            raise RuntimeError("Publisher is not started")

        message = aio_pika.Message(
            body=json.dumps(
                {"delivery_id": str(delivery_id)}
            ).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=QUEUE_NAME,
        )

    async def close(self) -> None:
        if self.channel is not None:
            await self.channel.close()