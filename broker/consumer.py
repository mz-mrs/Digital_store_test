import json
import logging

from aio_pika import Message

from app.broker.connection import create_connection
from app.db.session import async_session_factory
from app.services import PaymentService

from app.api.dependencies import get_provider_service
from broker.queques import setup_delivery

logger = logging.getLogger(__name__)

QUEUE_NAME = "delivery.issue"
MAX_RETRIES = 3

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

    await setup_delivery(channel)

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

                logger.error("Ошибка обработки delivery.issue")

                exchange = await channel.get_exchange("delivery")

                headers = message.headers or {}
                retry_count = int(headers.get("x-retry-count", 0))

                if retry_count >= MAX_RETRIES:
                    await exchange.publish(
                        Message(
                            body=message.body,
                            content_type=message.content_type,
                            delivery_mode=message.delivery_mode,
                            headers={
                                **message.headers,
                                "x-retry-count": retry_count,
                            },
                        ),
                        routing_key="dlq",
                    )

                    logger.error(
                        "Delivery отправлена в DLQ delivery_id=%s retry_count=%s",
                        json.loads(message.body)["delivery_id"],
                        retry_count,
                    )

                else:
                    retry_count += 1
                    await exchange.publish(
                        Message(
                            body=message.body,
                            content_type=message.content_type,
                            delivery_mode=message.delivery_mode,
                            headers={
                                **message.headers,
                                "x-retry-count": retry_count,
                            },
                        ),
                        routing_key="retry",
                    )

                    logger.warning(
                        "Delivery отправлена на retry delivery_id=%s retry_count=%s",
                        json.loads(message.body)["delivery_id"],
                        retry_count,
                    )

                await message.ack()

            else:
                await message.ack()