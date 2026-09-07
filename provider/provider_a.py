import uvicorn

from provider.app_provider import create_provider_app
from provider.provider_simulator import ProviderSimulator


provider = ProviderSimulator(
    name="A",
    error_chance=0.1,
    timeout_chance=0.1,
)

app = create_provider_app(provider)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
    )