from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel


DELIVERY_EXCHANGE = "delivery"

DELIVERY_ISSUE_QUEUE = "delivery.issue"
DELIVERY_RETRY_QUEUE = "delivery.retry"
DELIVERY_DLQ_QUEUE = "delivery.dlq"

DELIVERY_ISSUE_ROUTING_KEY = "issue"
DELIVERY_RETRY_ROUTING_KEY = "retry"
DELIVERY_DLQ_ROUTING_KEY = "dlq"


async def setup_delivery(channel: AbstractChannel) -> None:
    exchange = await channel.declare_exchange(
        DELIVERY_EXCHANGE,
        ExchangeType.DIRECT,
        durable=True,
    )

    issue_queue = await channel.declare_queue(
        DELIVERY_ISSUE_QUEUE,
        durable=True,
    )

    retry_queue = await channel.declare_queue(
        DELIVERY_RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": 10_000,
            "x-dead-letter-exchange": DELIVERY_EXCHANGE,
            "x-dead-letter-routing-key": DELIVERY_ISSUE_ROUTING_KEY,
        },
    )

    dlq_queue = await channel.declare_queue(
        DELIVERY_DLQ_QUEUE,
        durable=True,
    )

    await issue_queue.bind(
        exchange,
        routing_key=DELIVERY_ISSUE_ROUTING_KEY,
    )

    await retry_queue.bind(
        exchange,
        routing_key=DELIVERY_RETRY_ROUTING_KEY,
    )

    await dlq_queue.bind(
        exchange,
        routing_key=DELIVERY_DLQ_ROUTING_KEY,
    )