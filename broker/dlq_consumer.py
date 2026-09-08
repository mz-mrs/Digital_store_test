import json
import logging

from app.broker.connection import create_connection
from app.db.session import async_session_factory
from app.repositories import PaymentRepository

from broker.queques import setup_delivery

logger = logging.getLogger(__name__)

QUEUE_NAME = "delivery.dlq"


async def process_dlq_message(message) -> None:
    payload = json.loads(message.body)
    delivery_id = payload["delivery_id"]

    headers = message.headers or {}
    retry_count = int(headers.get("x-retry-count", 0))

    logger.error(
        "Получена задача из DLQ delivery_id=%s retry_count=%s",
        delivery_id,
        retry_count,
    )

    async with async_session_factory() as session:
        repository = PaymentRepository(session)

        delivery = await repository.get_delivery_for_update(
            delivery_id
        )

        if delivery is None:
            logger.error(
                "DLQ: delivery не найдена delivery_id=%s",
                delivery_id,
            )
            return

        logger.error(
            "DLQ: доставка требует восстановления delivery_id=%s order_id=%s status=%s retry_count=%s",
            delivery.id,
            delivery.order_id,
            delivery.status.value,
            retry_count,
        )

        await session.rollback()


async def consume_dlq() -> None:
    connection = await create_connection()
    channel = await connection.channel()

    await channel.set_qos(prefetch_count=1)

    await setup_delivery(channel)

    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
    )

    logger.info(
        "DLQ worker запущен, ожидание задач queue=%s",
        QUEUE_NAME,
    )

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                await process_dlq_message(message)

            except Exception:
                logger.exception("Ошибка обработки delivery.dlq")

                await message.nack(requeue=True)

            else:
                await message.ack()