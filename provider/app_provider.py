from fastapi import FastAPI

from provider.api.provider import create_provider_router
from provider.provider_simulator import ProviderSimulator


def create_provider_app(provider: ProviderSimulator) -> FastAPI:
    app = FastAPI()

    app.include_router(
        create_provider_router(provider)
    )

    return app
