import asyncio
import json
import logging

from aio_pika import DeliveryMode, Message

from app.broker.connection import create_connection
from app.db.session import async_session_factory
from app.repositories import PaymentRepository

from broker.queques import (
    DELIVERY_EXCHANGE,
    DELIVERY_ISSUE_ROUTING_KEY,
    setup_delivery,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30
STUCK_AFTER = 60


async def recover() -> None:
    connection = await create_connection()
    channel = await connection.channel()

    await setup_delivery(channel)

    exchange = await channel.get_exchange(
        DELIVERY_EXCHANGE
    )

    logger.info(
        "Recovery worker запущен interval=%s stuck_after=%s",
        CHECK_INTERVAL,
        STUCK_AFTER,
    )

    try:
        while True:
            try:
                async with async_session_factory() as session:
                    repository = PaymentRepository(session)

                    deliveries = (
                        await repository.get_stuck_deliveries(
                            older_than_seconds=STUCK_AFTER,
                        )
                    )

                    for delivery in deliveries:
                        message = Message(
                            body=json.dumps(
                                {
                                    "delivery_id": str(
                                        delivery.id
                                    )
                                }
                            ).encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                            content_type="application/json",
                        )

                        await exchange.publish(
                            message,
                            routing_key=DELIVERY_ISSUE_ROUTING_KEY,
                        )

                        logger.warning(
                            "Recovery: повторно отправлена delivery_id=%s order_id=%s",
                            delivery.id,
                            delivery.order_id,
                        )

            except Exception:
                logger.exception(
                    "Ошибка recovery worker"
                )

            await asyncio.sleep(CHECK_INTERVAL)

    finally:
        await channel.close()
        await connection.close()