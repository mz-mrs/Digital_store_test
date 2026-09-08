from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.orders import router as orders_router
from app.api.ckeck import router as check_router
from app.api.payment_webhook import router as payment_router

import logging

from app.broker.connection import create_connection
from app.broker.publisher import DeliveryPublisher

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = await create_connection()

    publisher = DeliveryPublisher(connection)
    await publisher.start()

    app.state.rabbitmq_connection = connection
    app.state.delivery_publisher = publisher

    yield

    await publisher.close()
    await connection.close()

app = FastAPI(lifespan=lifespan)

app.include_router(orders_router)
app.include_router(payment_router)
app.include_router(check_router)
