import json
import logging

import aio_pika

from app.broker.connection import create_connection
from app.clients import ProviderClient
from app.db.session import async_session_factory
from app.services import PaymentService
from app.services.provider_service import ProviderService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_NAME = "delivery.issue"


def get_provider_service() -> ProviderService:
    return ProviderService(
        providers=(
            ProviderClient(
                name="A",
                base_url="http://127.0.0.1:8001",
            ),
            ProviderClient(
                name="B",
                base_url="http://127.0.0.1:8002",
            ),
        ),
    )


async def process_message(message):

    payload = json.loads(message.body)

    delivery_id = payload["delivery_id"]

    logger.info(
        "Получена задача на выдачу delivery_id=%s",
        delivery_id,
    )

    async with async_session_factory() as session:

        service = PaymentService(
            session=session,
            provider_service=get_provider_service(),
        )

        await service.process_delivery(delivery_id)

    logger.info(
        "Задача на выдачу обработана delivery_id=%s",
        delivery_id,
    )


async def main() -> None:
    connection = await create_connection()

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
    )

    logger.info(
        "Worker запущен, ожидание задач queue=%s",
        QUEUE_NAME,
    )

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:

            try:
                await process_message(message)

            except Exception:
                logger.exception(
                    "Ошибка обработки delivery_id"
                )

                await message.nack(
                    requeue=False,
                )
            else:
                await message.ack()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())