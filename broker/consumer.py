import json
import logging

from app.broker.connection import create_connection
from app.db.session import async_session_factory
from app.services import PaymentService

from app.api.dependencies import get_provider_service

logger = logging.getLogger(__name__)

QUEUE_NAME = "delivery.issue"

async def process_message(message) -> None:
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


async def consume() -> None:
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
                    "Ошибка обработки delivery.issue"
                )

                await message.nack(requeue=False)

            else:
                await message.ack()