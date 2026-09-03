import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import OrderStatus, PaymentStatus
from app.models import Order, PaymentEvent
from app.repositories import PaymentRepository
from app.schemas.payment import PaymentWebhook

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PaymentRepository(session)

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

        order = await self.repository.get_order_for_update(
            payload.order_id
        )

        created_payment_event = await self.repository.create_payment_event(payload)


        if not created_payment_event:
            logger.info(
                "Вебхук повторный, игнор order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id
            )
            await self.session.rollback()
            return

        if order is None:
            logger.info(
                "Заказ еще не создан, вебхук сохранен order_id=%s event_id=%s",
                payload.order_id,
                payload.event_id,
            )
            await self.session.commit()
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

