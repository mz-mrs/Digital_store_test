from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.order import OrderRepository
from app.services import OrderService, PaymentService
from app.clients import ProviderClient
from app.services import ProviderService


def get_order_service(
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    repository = OrderRepository(session)
    return OrderService(repository)

def get_order_repository(
    session: AsyncSession = Depends(get_session),
) -> OrderRepository:
    return OrderRepository(session)


def get_provider_service() -> ProviderService:
    return ProviderService(
        providers=(
            ProviderClient(
                name="A",
                base_url="http://127.0.0.1:8001",
            ),
            ProviderClient(
                name="B",
                base_url="http://127.0.0.1:8002",
            ),
        ),
    )


def get_payment_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
    provider_service: ProviderService = Depends(get_provider_service),
) -> PaymentService:
    return PaymentService(
        session=session,
        provider_service=provider_service,
        publisher=request.app.state.delivery_publisher,
    )