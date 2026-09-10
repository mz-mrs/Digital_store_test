import pytest_asyncio
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import Delivery, Order, OrderItem, PaymentEvent


@pytest_asyncio.fixture
async def cleanup_orders():
    order_ids: list[str] = []

    def register(order_id: str) -> str:
        order_ids.append(order_id)
        return order_id

    yield register

    if not order_ids:
        return

    async with async_session_factory() as session:
        await session.execute(
            delete(PaymentEvent).where(
                PaymentEvent.order_id.in_(order_ids)
            )
        )
        await session.execute(
            delete(Delivery).where(
                Delivery.order_id.in_(order_ids)
            )
        )
        await session.execute(
            delete(OrderItem).where(
                OrderItem.order_id.in_(order_ids)
            )
        )
        await session.execute(
            delete(Order).where(
                Order.id.in_(order_ids)
            )
        )

        await session.commit()