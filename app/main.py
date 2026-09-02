from fastapi import FastAPI

from app.api.orders import router as orders_router

import logging

logging.basicConfig(level=logging.INFO)


app = FastAPI()

app.include_router(orders_router)