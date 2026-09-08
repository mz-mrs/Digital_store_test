from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import DeliveryStatus, PaymentStatus, OrderStatus
from app.models import Order, PaymentEvent, Delivery
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
            .options(selectinload(Order.items))
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

    async def get_delivery_for_update(
            self,
            delivery_id: int,
    ) -> Delivery | None:
        return await self.session.scalar(
            select(Delivery)
            .where(Delivery.id == delivery_id)
            .with_for_update()
        )

    async def get_paid_not_delivered(self) -> list:
        latest_payment = (
            select(
                PaymentEvent.order_id,
                func.max(PaymentEvent.created_at).label("latest_created_at"),
            )
            .group_by(PaymentEvent.order_id)
            .subquery()
        )

        result = await self.session.execute(
            select(Order, Delivery)
            .join(
                Delivery,
                Delivery.order_id == Order.id,
            )
            .join(
                latest_payment,
                latest_payment.c.order_id == Order.id,
            )
            .join(
                PaymentEvent,
                (PaymentEvent.order_id == Order.id)
                & (
                        PaymentEvent.created_at
                        == latest_payment.c.latest_created_at
                ),
            )
            .where(
                PaymentEvent.status == PaymentStatus.PAID,
                Delivery.status != DeliveryStatus.DELIVERED,
            )
        )

        return list(result.all())


    async def get_delivered_not_paid(self) -> list:
        latest_payment = (
            select(
                PaymentEvent.order_id,
                func.max(PaymentEvent.created_at).label("latest_created_at"),
            )
            .group_by(PaymentEvent.order_id)
            .subquery()
        )

        result = await self.session.execute(
            select(Order, Delivery)
            .join(
                Delivery,
                Delivery.order_id == Order.id,
            )
            .join(
                latest_payment,
                latest_payment.c.order_id == Order.id,
            )
            .join(
                PaymentEvent,
                (PaymentEvent.order_id == Order.id)
                & (
                        PaymentEvent.created_at
                        == latest_payment.c.latest_created_at
                ),
            )
            .where(
                PaymentEvent.status != PaymentStatus.PAID,
                Delivery.status == DeliveryStatus.DELIVERED,
            )
        )

        return list(result.all())

    async def get_pending_deliveries(self) -> list[Delivery]:
        result = await self.session.execute(
            select(Delivery)
            .join(Order, Delivery.order_id == Order.id)
            .join(PaymentEvent, PaymentEvent.order_id == Order.id)
            .where(
                Order.status == OrderStatus.PAID,
                Delivery.status == DeliveryStatus.PENDING,
                PaymentEvent.status == PaymentStatus.PAID,
            )
            .distinct(Delivery.id)
        )

        return list(result.scalars().all())


    async def get_stuck_deliveries(
        self,
        older_than_seconds: int = 60,
    ) -> list[Delivery]:
        threshold = datetime.now(timezone.utc) - timedelta(
            seconds=older_than_seconds
        )

        result = await self.session.execute(
            select(Delivery)
            .join(Order, Delivery.order_id == Order.id)
            .where(
                Order.status == OrderStatus.PAID,
                Delivery.status == DeliveryStatus.PENDING,
                Delivery.updated_at < threshold,
            )
            .with_for_update(skip_locked=True)
        )

        return list(result.scalars().all())

