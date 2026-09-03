from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, PaymentEvent
from app.schemas.payment import PaymentWebhook


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_order_for_update(
        self,
        order_id: str,
    ) -> Order | None:

        return await self.session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        )

    async def create_payment_event(
        self,
        payload: PaymentWebhook,
    ) -> bool:

        statement = (
            insert(PaymentEvent)
            .values(
                event_id=payload.event_id,
                order_id=payload.order_id,
                status=payload.status,
                amount=payload.amount,
                currency=payload.currency,
                created_at=payload.created_at,
            )
            .on_conflict_do_nothing(
                index_elements=[PaymentEvent.event_id],
            )
        )

        result = await self.session.execute(statement)

        return result.rowcount == 1