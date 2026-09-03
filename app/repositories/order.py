from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Order, Product, PaymentEvent


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_product_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalar_one_or_none()

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()

        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_event(
        self,
        order_id: str,
    ) -> PaymentEvent | None:
        result = await self.session.execute(
            select(PaymentEvent)
            .where(PaymentEvent.order_id == order_id)
            .order_by(PaymentEvent.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()