from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.order import OrderRepository
from app.services.order import OrderService


def get_order_service(
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    repository = OrderRepository(session)
    return OrderService(repository)