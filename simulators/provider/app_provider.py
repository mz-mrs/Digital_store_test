import logging

from fastapi import FastAPI

from simulators.provider.api.provider import create_provider_router
from simulators.provider.provider_simulator import ProviderSimulator

logging.basicConfig(level=logging.INFO)

def create_provider_app(provider: ProviderSimulator) -> FastAPI:
    app = FastAPI()

    app.include_router(
        create_provider_router(provider)
    )

    return app
