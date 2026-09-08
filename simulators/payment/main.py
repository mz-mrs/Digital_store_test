import logging

from fastapi import FastAPI

from simulators.payment.api import create_payment_router
from simulators.payment.payment_simulator import PaymentSimulator


logging.basicConfig(level=logging.INFO)

WEBHOOK_URL = "http://127.0.0.1:8000/webhook/payment"
API_URL = "http://127.0.0.1:8000"


def create_payment_app() -> FastAPI:
    app = FastAPI(
        title="Payment Simulator",
    )

    simulator = PaymentSimulator(
        webhook_url=WEBHOOK_URL,
        api_url=API_URL
    )

    app.include_router(
        create_payment_router(simulator)
    )

    return app


app = create_payment_app()