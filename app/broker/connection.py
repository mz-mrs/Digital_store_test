import aio_pika

from app.core.settings import settings


async def create_connection() -> aio_pika.abc.AbstractRobustConnection:
    return await aio_pika.connect_robust(
        settings.rabbitmq_url
    )