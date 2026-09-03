from fastapi import FastAPI

from app.api.orders import router as orders_router
from app.api.payment_webhook import router as payment_router

import logging

logging.basicConfig(level=logging.INFO)


app = FastAPI()

app.include_router(orders_router)
app.include_router(payment_router)