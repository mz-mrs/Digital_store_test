from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import PaymentRepository
from app.schemas.ckecker import CheckingItem, CheckingItemResponse


class CheckService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = PaymentRepository(session)

    async def check_items(self) -> CheckingItemResponse:
        paid_not_delivered = (
            await self.repository.get_paid_not_delivered()
        )

        delivered_not_paid = (
            await self.repository.get_delivered_not_paid()
        )

        return CheckingItemResponse(
            paid_not_delivered=[
                CheckingItem(
                    order_id=order.id,
                    delivery_id=str(delivery.id),
                    order_status=order.status.value,
                    delivery_status=delivery.status.value,
                )
                for order, delivery in paid_not_delivered
            ],
            delivered_not_paid=[
                CheckingItem(
                    order_id=order.id,
                    delivery_id=str(delivery.id),
                    order_status=order.status.value,
                    delivery_status=delivery.status.value,
                )
                for order, delivery in delivered_not_paid
            ],
        )

    async def get_paid_not_delivered(self):
        return await self.repository.get_paid_not_delivered()