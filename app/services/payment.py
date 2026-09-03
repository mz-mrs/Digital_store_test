import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import OrderStatus, PaymentStatus
from app.models import Order, PaymentEvent
from app.schemas.payment import PaymentWebhook

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def process_webhook(
        self,
        payload: PaymentWebhook,
    ) -> None:

        logger.info(
            "Получен вебхук event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            payload.status.value
        )

        order = await self.session.scalar(
            select(Order)
            .where(Order.id == payload.order_id)
            .with_for_update()
        )

        if order is None:
            logger.warning(
                "Вебхук отклонен, заказ не найден order_id=%s",
                payload.order_id
            )
            raise ValueError("Заказ не найден")

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

        if result.rowcount == 0:
            logger.info(
                "Вебхук повторный, игнор order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )
            await self.session.rollback()
            return

        logger.info(
            "Вебхук оплаты прошел проверку успешно event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            payload.status.value
        )

        if order.status != OrderStatus.CREATED:

            await self.session.commit()
            logger.info(
                "Невозможно обработать вебхук event_id=%s order_id=%s, статус заказа %s",
                payload.event_id,
                payload.order_id,
                order.status.value
            )
            return

        if payload.status == PaymentStatus.PAID:
            order.status = OrderStatus.PAID

            logger.info(
                "Заказ оплачен успешно order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )

        else:
            logger.info(
                "Статус заказа не оплачен order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )

            order.status = OrderStatus.PAYMENT_FAILED

        await self.session.commit()

        logger.info(
            "Вебхук обработан event_id=%s order_id=%s status=%s",
            payload.event_id,
            payload.order_id,
            order.status
        )

