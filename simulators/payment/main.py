import logging

from fastapi import FastAPI

from app.core.settings import settings
from simulators.payment.api import create_payment_router
from simulators.payment.payment_simulator import PaymentSimulator


logging.basicConfig(level=logging.INFO)



def create_payment_app() -> FastAPI:
    app = FastAPI(
        title="Payment Simulator",
    )

    simulator = PaymentSimulator(
        webhook_url=settings.webhook_url,
        api_url=settings.api_url
    )

    app.include_router(
        create_payment_router(simulator)
    )

    return app


app = create_payment_app()